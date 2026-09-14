from datetime import date


def test_dashboard_summary_matches_manual_counts(auth_client):
    auth_client.post(
        "/tasks", json={"title": "Pendiente 1", "priority": "high", "estimatedHours": 1}
    )
    auth_client.post(
        "/tasks", json={"title": "Pendiente 2", "priority": "low", "estimatedHours": 1}
    )
    completed = auth_client.post(
        "/tasks", json={"title": "Completada", "priority": "high", "estimatedHours": 1}
    ).json()
    auth_client.patch(f"/tasks/{completed['id']}/complete")
    auth_client.post(
        "/tasks",
        json={
            "title": "Vence hoy",
            "priority": "medium",
            "estimatedHours": 1,
            "dueDate": date.today().isoformat(),
        },
    )

    summary = auth_client.get("/dashboard").json()["summary"]

    assert summary["total"] == 4
    assert summary["completed"] == 1
    assert summary["pending"] == 3
    assert summary["highPriorityCount"] == 2
    assert summary["dueToday"] == 1


def test_dashboard_priority_list_excludes_completed(auth_client):
    high_completed = auth_client.post(
        "/tasks", json={"title": "Alta completada", "priority": "high", "estimatedHours": 1}
    ).json()
    auth_client.patch(f"/tasks/{high_completed['id']}/complete")
    auth_client.post(
        "/tasks", json={"title": "Alta pendiente", "priority": "high", "estimatedHours": 1}
    )

    priority_titles = [item["title"] for item in auth_client.get("/dashboard").json()["priority"]]
    assert priority_titles == ["Alta pendiente"]


def test_dashboard_empty_for_new_user(auth_client):
    dashboard = auth_client.get("/dashboard").json()
    assert dashboard["summary"]["total"] == 0
    assert dashboard["upcoming"] == dashboard["priority"] == dashboard["recent"] == []
