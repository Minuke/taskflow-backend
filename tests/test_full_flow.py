def test_complete_user_journey(client):
    register_response = client.post(
        "/auth/register",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "password": "unacontraseñasegura",
            "confirmPassword": "unacontraseñasegura",
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    category_id = client.post("/categories", json={"name": "Backend", "description": None}).json()[
        "id"
    ]

    task_response = client.post(
        "/tasks",
        json={
            "title": "Estudiar FastAPI",
            "description": "Repasar dependencias e inyección",
            "priority": "high",
            "estimatedHours": 4,
            "categoryId": category_id,
        },
    )
    task_id = task_response.json()["id"]
    assert task_response.json()["completed"] is False

    complete_response = client.patch(f"/tasks/{task_id}/complete")
    assert complete_response.json()["completed"] is True

    dashboard = client.get("/dashboard").json()
    assert dashboard["summary"]["total"] == 1
    assert dashboard["summary"]["completed"] == 1

    assert (
        client.post(
            "/auth/login", data={"username": "ana@example.com", "password": "unacontraseñasegura"}
        ).status_code
        == 200
    )

    assert client.post("/auth/logout").status_code == 204
