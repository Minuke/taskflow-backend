from datetime import date, timedelta


def test_sort_by_due_date_breaks_ties_by_priority(auth_client):
    same_due_date = (date.today() + timedelta(days=10)).isoformat()

    auth_client.post(
        "/tasks",
        json={"title": "Baja", "priority": "low", "estimatedHours": 1, "dueDate": same_due_date},
    )
    auth_client.post(
        "/tasks",
        json={"title": "Alta", "priority": "high", "estimatedHours": 1, "dueDate": same_due_date},
    )
    auth_client.post(
        "/tasks",
        json={"title": "Media", "priority": "medium", "estimatedHours": 1, "dueDate": same_due_date},
    )

    response = auth_client.get("/tasks?sort_by=dueDate&order=asc")
    titles = [item["title"] for item in response.json()["items"]]

    assert titles == ["Alta", "Media", "Baja"]


def test_tasks_without_due_date_go_last_regardless_of_order(auth_client):
    auth_client.post("/tasks", json={"title": "Sin fecha", "priority": "medium", "estimatedHours": 1})
    auth_client.post(
        "/tasks",
        json={
            "title": "Con fecha",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": (date.today() + timedelta(days=5)).isoformat(),
        },
    )

    for order in ("asc", "desc"):
        titles = [
            item["title"]
            for item in auth_client.get(f"/tasks?sort_by=dueDate&order={order}").json()["items"]
        ]
        assert titles[-1] == "Sin fecha"