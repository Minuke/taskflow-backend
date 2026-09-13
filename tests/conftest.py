"""
IMPORTANTE: la sobrescritura de variables de entorno con .env.test debe ejecutarse
ANTES de cualquier "from app...." de este archivo. En cuanto Python importa por
primera vez app.core.config, el singleton `settings` queda fijado con los valores
que haya en ese momento, y ya no se puede cambiar durante el resto de la sesión.
"""

from pathlib import Path

from dotenv import load_dotenv

ENV_TEST_PATH = Path(__file__).resolve().parent.parent / ".env.test"
load_dotenv(ENV_TEST_PATH, override=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402

if "test" not in settings.database_url:
    raise RuntimeError(
        "La URL de la base de datos no contiene 'test'. Por seguridad, los tests "
        "solo se ejecutan contra una base de datos claramente identificada como de "
        "pruebas. Revisa tu archivo .env.test."
    )

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def register_user(client):
    def _register(email: str = "ana@example.com", password: str = "unacontraseñasegura") -> dict:
        response = client.post(
            "/auth/register",
            json={
                "name": "Ana",
                "email": email,
                "password": password,
                "confirmPassword": password,
            },
        )
        assert response.status_code == 201
        return response.json()

    return _register


@pytest.fixture
def auth_client(client, register_user):
    token = register_user()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client