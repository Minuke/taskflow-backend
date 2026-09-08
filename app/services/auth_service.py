from datetime import datetime, timedelta, timezone

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, generate_refresh_token, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import Token

REFRESH_COOKIE_PATH = "/auth"


class InvalidRefreshTokenError(Exception):
    """El refresh token presentado no existe, ya fue revocado, o ha expirado."""


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=raw_refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def issue_token_pair(db: Session, user: User, response: Response) -> Token:
    access_token = create_access_token(subject=str(user.id))

    raw_refresh_token = generate_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(refresh_token)
    db.commit()

    _set_refresh_cookie(response, raw_refresh_token)
    return Token(access_token=access_token)


def rotate_refresh_token(db: Session, raw_refresh_token: str, response: Response) -> Token:
    token_hash = hash_refresh_token(raw_refresh_token)
    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    now = datetime.now(timezone.utc)
    if stored_token is None or stored_token.revoked_at is not None or stored_token.expires_at < now:
        raise InvalidRefreshTokenError()

    stored_token.revoked_at = now
    db.add(stored_token)

    user = db.get(User, stored_token.user_id)
    if user is None:
        raise InvalidRefreshTokenError()

    return issue_token_pair(db, user, response)


def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)
    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if stored_token is not None and stored_token.revoked_at is None:
        stored_token.revoked_at = datetime.now(timezone.utc)
        db.add(stored_token)
        db.commit()