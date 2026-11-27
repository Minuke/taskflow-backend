import pytest

from app.core.translations import translate_http_detail, translate_validation_error


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        ({"type": "missing", "msg": "Field required"}, "Este campo es obligatorio."),
        (
            {"type": "string_too_short", "msg": "x", "ctx": {"min_length": 3}},
            "Debe tener al menos 3 caracteres.",
        ),
        (
            {"type": "string_too_short", "msg": "x", "ctx": {"min_length": 1}},
            "Este campo es obligatorio.",
        ),
        (
            {"type": "string_too_long", "msg": "x", "ctx": {"max_length": 80}},
            "No puede superar los 80 caracteres.",
        ),
        (
            {"type": "greater_than_equal", "msg": "x", "ctx": {"ge": 1}},
            "Debe ser mayor o igual que 1.",
        ),
        (
            {"type": "less_than_equal", "msg": "x", "ctx": {"le": 10}},
            "Debe ser menor o igual que 10.",
        ),
        (
            {"type": "enum", "msg": "x", "ctx": {"expected": "'low', 'medium' or 'high'"}},
            "Valor no permitido. Valores válidos: 'low', 'medium' o 'high'.",
        ),
        ({"type": "int_parsing", "msg": "x"}, "Debe ser un número entero."),
        (
            {"type": "decimal_max_places", "msg": "x", "ctx": {"decimal_places": 2}},
            "No puede tener más de 2 decimales.",
        ),
        (
            {
                "type": "value_error",
                "msg": "value is not a valid email address: An email address must have an @-sign.",
            },
            "Introduce un email válido.",
        ),
        (
            {"type": "value_error", "msg": "Value error, Las contraseñas no coinciden."},
            "Las contraseñas no coinciden.",
        ),
        # Tipo desconocido: se conserva el texto original.
        ({"type": "tipo_nuevo", "msg": "Some English text"}, "Some English text"),
        # Plantilla sin el dato en ctx: no falla, devuelve el original.
        ({"type": "string_too_short", "msg": "Original", "ctx": {}}, "Original"),
    ],
)
def test_translate_validation_error(error, expected):
    assert translate_validation_error(error) == expected


def test_translate_http_detail():
    assert translate_http_detail("Not Found") == "Recurso no encontrado."
    assert translate_http_detail("Tarea no encontrada.") == "Tarea no encontrada."


def test_register_with_missing_fields_returns_spanish_messages(client):
    response = client.post("/auth/register", json={"name": "Ana"})

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert errors, "Debe haber errores de validación"
    assert all(error["message"] == "Este campo es obligatorio." for error in errors)
