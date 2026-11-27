import pytest

from app.core.config import settings
from app.core.rate_limit import login_limiter, register_limiter

LOGIN_DATA = {"username": "nadie@example.com", "password": "incorrecta"}


@pytest.fixture(autouse=True)
def enable_rate_limit(monkeypatch):
    # El resto de tests lo tienen desactivado (.env.test); aquí lo activamos.
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    login_limiter.reset()
    register_limiter.reset()
    yield
    login_limiter.reset()
    register_limiter.reset()


def test_login_is_blocked_after_too_many_attempts(client):
    for _ in range(login_limiter.max_attempts):
        assert client.post("/auth/login", data=LOGIN_DATA).status_code == 401

    response = client.post("/auth/login", data=LOGIN_DATA)

    assert response.status_code == 429
    assert response.headers["Retry-After"].isdigit()
    assert response.json()["detail"].startswith("Demasiados intentos.")


def test_register_is_blocked_after_too_many_attempts(client):
    for _ in range(register_limiter.max_attempts):
        assert client.post("/auth/register", json={}).status_code == 422

    response = client.post("/auth/register", json={})

    assert response.status_code == 429


def test_limits_are_independent_per_endpoint(client):
    for _ in range(login_limiter.max_attempts + 1):
        client.post("/auth/login", data=LOGIN_DATA)

    # El login está bloqueado, pero el registro sigue disponible.
    assert client.post("/auth/register", json={}).status_code == 422


def test_rate_limit_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", False)

    statuses = {
        client.post("/auth/login", data=LOGIN_DATA).status_code
        for _ in range(login_limiter.max_attempts + 5)
    }

    assert statuses == {401}
