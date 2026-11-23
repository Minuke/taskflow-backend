def test_estimated_hours_is_serialized_as_number(auth_client):
    response = auth_client.post(
        "/tasks",
        json={"title": "Tarea con decimales", "priority": "medium", "estimatedHours": 2.5},
    )
    assert response.status_code == 201
    assert response.json()["estimatedHours"] == 2.5
