def _create_task(auth_client, **overrides):
    payload = {"title": "Tarea", "priority": "medium", "estimatedHours": 1}
    payload.update(overrides)
    response = auth_client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_search_matches_title_or_description(auth_client):
    _create_task(auth_client, title="Estudiar FastAPI")
    _create_task(auth_client, title="Comprar comida", description="Repasar FastAPI luego")
    _create_task(auth_client, title="Otra cosa", description="Nada relacionado")

    response = auth_client.get("/tasks?search=fastapi")
    assert response.json()["total"] == 2


def test_status_and_priority_filters_combine(auth_client):
    high = _create_task(auth_client, title="Alta pendiente", priority="high")
    _create_task(auth_client, title="Baja pendiente", priority="low")
    auth_client.patch(f"/tasks/{high['id']}/complete")

    response = auth_client.get("/tasks?status=pending&priority=low")
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Baja pendiente"


def test_category_filter(auth_client):
    category_id = auth_client.post("/categories", json={"name": "Backend"}).json()["id"]
    _create_task(auth_client, title="Con categoría", categoryId=category_id)
    _create_task(auth_client, title="Sin categoría")

    response = auth_client.get(f"/tasks?category_id={category_id}")
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Con categoría"


def test_pagination_metadata(auth_client):
    for i in range(12):
        _create_task(auth_client, title=f"Tarea {i}")

    page_1 = auth_client.get("/tasks?page=1&page_size=10").json()
    assert len(page_1["items"]) == 10
    assert page_1["total"] == 12
    assert page_1["totalPages"] == 2

    page_2 = auth_client.get("/tasks?page=2&page_size=10").json()
    assert len(page_2["items"]) == 2
