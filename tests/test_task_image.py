import io

from PIL import Image


def _make_test_image_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_valid_image(auth_client):
    task_id = auth_client.post(
        "/tasks", json={"title": "Con imagen", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]

    response = auth_client.post(
        f"/tasks/{task_id}/image",
        files={"file": ("foto.png", _make_test_image_bytes(), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["image"].startswith("/media/tasks/")


def test_upload_rejects_non_image_file(auth_client):
    task_id = auth_client.post(
        "/tasks", json={"title": "Archivo falso", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]

    response = auth_client.post(
        f"/tasks/{task_id}/image",
        files={"file": ("documento.png", b"esto no es una imagen", "image/png")},
    )
    assert response.status_code == 422


def test_delete_image_removes_it(auth_client):
    task_id = auth_client.post(
        "/tasks", json={"title": "Tarea", "priority": "medium", "estimatedHours": 1}
    ).json()["id"]
    auth_client.post(
        f"/tasks/{task_id}/image",
        files={"file": ("foto.png", _make_test_image_bytes(), "image/png")},
    )

    response = auth_client.delete(f"/tasks/{task_id}/image")
    assert response.status_code == 200
    assert response.json()["image"] is None
