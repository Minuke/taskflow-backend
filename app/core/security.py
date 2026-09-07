from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

# Hash "señuelo" precalculado una sola vez al arrancar la aplicación.
# Se usa en el login cuando el email no existe, para que verificar una contraseña
# tarde siempre lo mismo exista o no el usuario, evitando ataques de timing
# (que alguien deduzca qué emails están registrados midiendo tiempos de respuesta).
DUMMY_PASSWORD_HASH = password_hash.hash("dummy-password-for-timing-safety")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)