def test_create_task_ignores_completed_field_in_payload(auth_client):
    response = auth_client.post(
        "/tasks",
        json={
            "title": "Intento crear ya completada",
            "priority": "medium",
            "estimatedHours": 1,
            "completed": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["completed"] is False


def test_update_task_ignores_completed_field_in_payload(auth_client):
    task_id = auth_client.post(
        "/tasks", json={"title": "Tarea pendiente", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]

    update_response = auth_client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Tarea pendiente",
            "priority": "medium",
            "estimatedHours": 1,
            "categoryId": None,
            "completed": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["completed"] is False


def test_only_complete_endpoint_marks_task_as_completed(auth_client):
    task_id = auth_client.post(
        "/tasks", json={"title": "Tarea a completar", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]

    complete_response = auth_client.patch(f"/tasks/{task_id}/complete")
    assert complete_response.json()["completed"] is True