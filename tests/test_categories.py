def test_create_list_update_delete_category(auth_client):
    category_id = auth_client.post(
        "/categories", json={"name": "Backend", "description": "Tareas de backend"}
    ).json()["id"]

    list_response = auth_client.get("/categories")
    assert list_response.json()[0]["taskCount"] == 0

    update_response = auth_client.put(
        f"/categories/{category_id}", json={"name": "Backend Actualizado", "description": None}
    )
    assert update_response.json()["name"] == "Backend Actualizado"

    assert auth_client.delete(f"/categories/{category_id}").status_code == 204
    assert auth_client.get(f"/categories/{category_id}").status_code == 404


def test_deleting_category_unlinks_tasks_without_deleting_them(auth_client):
    category_id = auth_client.post("/categories", json={"name": "Temporal"}).json()["id"]
    task_id = auth_client.post(
        "/tasks",
        json={
            "title": "Tarea vinculada",
            "priority": "medium",
            "estimatedHours": 1,
            "categoryId": category_id,
        },
    ).json()["id"]

    auth_client.delete(f"/categories/{category_id}")

    task_response = auth_client.get(f"/tasks/{task_id}")
    assert task_response.status_code == 200
    assert task_response.json()["categoryId"] is None