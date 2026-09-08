from datetime import datetime, timedelta, timezone
import hashlib
import secrets
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

def generate_refresh_token() -> str:
    """Genera un token opaco con 256 bits de entropía criptográficamente segura."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    """SHA-256: rápido y determinista, suficiente para un valor ya de alta entropía
    (a diferencia de las contraseñas, que necesitan un hash lento como Argon2)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()