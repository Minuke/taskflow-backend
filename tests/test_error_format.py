def test_validation_error_has_field_and_readable_message(client):
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
    assert response.json()["errors"] == [
        {"field": "password", "message": "La contraseña debe tener al menos 8 caracteres."}
    ]
