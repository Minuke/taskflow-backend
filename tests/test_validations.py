from datetime import date, timedelta

from app.models.task import Task


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "corta1",
            "confirmPassword": "corta1",
        },
    )
    assert response.status_code == 422


def test_register_rejects_mismatched_passwords(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "unacontraseñasegura",
            "confirmPassword": "otradistinta",
        },
    )
    assert response.status_code == 422


def test_register_rejects_duplicate_email(client, register_user):
    register_user(email="ana@example.com")
    response = client.post(
        "/auth/register",
        json={
            "name": "Otra Ana",
            "email": "ana@example.com",
            "password": "unacontraseñasegura",
            "confirmPassword": "unacontraseñasegura",
        },
    )
    assert response.status_code == 409


def test_login_wrong_password_returns_generic_message(client, register_user):
    register_user(email="ana@example.com", password="unacontraseñasegura")
    response = client.post(
        "/auth/login",
        data={"username": "ana@example.com", "password": "incorrecta"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email o contraseña incorrectos."


def test_create_task_rejects_short_title(auth_client):
    response = auth_client.post(
        "/tasks", json={"title": "Ab", "priority": "medium", "estimatedHours": 1}
    )
    assert response.status_code == 422


def test_create_task_rejects_negative_estimated_hours(auth_client):
    response = auth_client.post(
        "/tasks", json={"title": "Tarea válida", "priority": "medium", "estimatedHours": -1}
    )
    assert response.status_code == 422


def test_create_task_rejects_past_due_date(auth_client):
    response = auth_client.post(
        "/tasks",
        json={
            "title": "Tarea con fecha pasada",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": "2000-01-01",
        },
    )
    assert response.status_code == 422


def test_update_task_allows_keeping_past_due_date_if_untouched(auth_client, db_session):
    create_response = auth_client.post(
        "/tasks",
        json={
            "title": "Tarea que acabará vencida",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": (date.today() + timedelta(days=1)).isoformat(),
        },
    )
    task_id = create_response.json()["id"]

    # Simulamos el paso del tiempo: la tarea "envejece" y su fecha límite
    # queda en el pasado, sin que el usuario haya tocado nada todavía.
    task = db_session.get(Task, task_id)
    task.due_date = date.today() - timedelta(days=5)
    db_session.commit()

    update_response = auth_client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Título actualizado, sin tocar la fecha",
            "priority": "high",
            "estimatedHours": 2,
            "dueDate": (date.today() - timedelta(days=5)).isoformat(),
            "categoryId": None,
        },
    )
    assert update_response.status_code == 200


def test_update_task_rejects_new_past_due_date(auth_client):
    create_response = auth_client.post(
        "/tasks",
        json={
            "title": "Tarea con fecha futura",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": (date.today() + timedelta(days=1)).isoformat(),
        },
    )
    task_id = create_response.json()["id"]

    update_response = auth_client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Intento cambiar a otra fecha pasada",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": (date.today() - timedelta(days=1)).isoformat(),
            "categoryId": None,
        },
    )
    assert update_response.status_code == 422