from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead
from app.services.auth_service import (
    InvalidRefreshTokenError,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, response: Response, db: DbSession) -> Token:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ese email ya está registrado.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return issue_token_pair(db, user, response)


@router.post("/login")
def login(
    response: Response,
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = db.scalar(select(User).where(User.email == form_data.username))

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email o contraseña incorrectos.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        verify_password(form_data.password, DUMMY_PASSWORD_HASH)
        raise invalid_credentials

    if not verify_password(form_data.password, user.password_hash):
        raise invalid_credentials

    return issue_token_pair(db, user, response)


@router.post("/refresh")
def refresh(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=settings.refresh_token_cookie_name)] = None,
) -> Token:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No hay sesión activa."
        )

    try:
        return rotate_refresh_token(db, refresh_token, response)
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado o no es válida. Inicia sesión de nuevo.",
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=settings.refresh_token_cookie_name)] = None,
) -> None:
    if refresh_token is not None:
        revoke_refresh_token(db, refresh_token)
    response.delete_cookie(key=settings.refresh_token_cookie_name, path="/auth")


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> User:
    return current_user
