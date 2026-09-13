def test_cannot_access_another_users_category(client, register_user):
    user_a = register_user(email="a@example.com")
    client.headers["Authorization"] = f"Bearer {user_a['access_token']}"
    category_id = client.post("/categories", json={"name": "Backend"}).json()["id"]

    user_b = register_user(email="b@example.com")
    client.headers["Authorization"] = f"Bearer {user_b['access_token']}"

    assert client.get(f"/categories/{category_id}").status_code == 404
    assert client.put(f"/categories/{category_id}", json={"name": "Hackeada"}).status_code == 404
    assert client.delete(f"/categories/{category_id}").status_code == 404


def test_cannot_access_another_users_task(client, register_user):
    user_a = register_user(email="a@example.com")
    client.headers["Authorization"] = f"Bearer {user_a['access_token']}"
    task_id = client.post(
        "/tasks", json={"title": "Tarea de A", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]

    user_b = register_user(email="b@example.com")
    client.headers["Authorization"] = f"Bearer {user_b['access_token']}"

    assert client.get(f"/tasks/{task_id}").status_code == 404
    assert client.patch(f"/tasks/{task_id}/complete").status_code == 404
    assert client.delete(f"/tasks/{task_id}").status_code == 404


def test_cannot_assign_task_to_another_users_category(client, register_user):
    user_a = register_user(email="a@example.com")
    client.headers["Authorization"] = f"Bearer {user_a['access_token']}"
    category_id = client.post("/categories", json={"name": "Backend"}).json()["id"]

    user_b = register_user(email="b@example.com")
    client.headers["Authorization"] = f"Bearer {user_b['access_token']}"

    response = client.post(
        "/tasks",
        json={
            "title": "Intento colar categoría ajena",
            "priority": "medium",
            "estimatedHours": 1,
            "categoryId": category_id,
        },
    )
    assert response.status_code == 404