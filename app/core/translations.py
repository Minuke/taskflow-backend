"""Traducción al español de los mensajes que genera el framework por defecto."""

from collections.abc import Mapping
from typing import Any

REQUIRED_MESSAGE = "Este campo es obligatorio."
EMAIL_PREFIX = "value is not a valid email address"

# Clave: `type` del error de Pydantic. Valor: plantilla que se rellena con `ctx`.
_VALIDATION_MESSAGES: dict[str, str] = {
    "missing": REQUIRED_MESSAGE,
    "string_type": "Debe ser un texto.",
    "string_too_short": "Debe tener al menos {min_length} caracteres.",
    "string_too_long": "No puede superar los {max_length} caracteres.",
    "string_pattern_mismatch": "El formato no es válido.",
    "greater_than": "Debe ser mayor que {gt}.",
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    "less_than": "Debe ser menor que {lt}.",
    "less_than_equal": "Debe ser menor o igual que {le}.",
    "int_parsing": "Debe ser un número entero.",
    "int_type": "Debe ser un número entero.",
    "float_parsing": "Debe ser un número.",
    "float_type": "Debe ser un número.",
    "decimal_parsing": "Debe ser un número.",
    "decimal_type": "Debe ser un número.",
    "decimal_max_digits": "No puede tener más de {max_digits} dígitos en total.",
    "decimal_max_places": "No puede tener más de {decimal_places} decimales.",
    "decimal_whole_digits": "Tiene demasiados dígitos enteros.",
    "bool_parsing": "Debe ser verdadero o falso.",
    "bool_type": "Debe ser verdadero o falso.",
    "enum": "Valor no permitido. Valores válidos: {expected}.",
    "literal_error": "Valor no permitido. Valores válidos: {expected}.",
    "date_parsing": "Debe ser una fecha válida (AAAA-MM-DD).",
    "date_type": "Debe ser una fecha válida (AAAA-MM-DD).",
    "date_from_datetime_parsing": "Debe ser una fecha válida (AAAA-MM-DD).",
    "too_short": "Debe tener al menos {min_length} elementos.",
    "too_long": "No puede tener más de {max_length} elementos.",
    "extra_forbidden": "Este campo no está permitido.",
    "json_invalid": "El cuerpo de la petición no es un JSON válido.",
}

# Detalles que FastAPI/Starlette generan por su cuenta (nuestras HTTPException ya están en español).
_HTTP_DETAILS: dict[str, str] = {
    "Not Found": "Recurso no encontrado.",
    "Method Not Allowed": "Método no permitido.",
    "Not authenticated": "No has iniciado sesión.",
    "Forbidden": "No tienes permiso para realizar esta acción.",
}


def translate_validation_error(error: Mapping[str, Any]) -> str:
    """Devuelve el mensaje en español de un error de validación de Pydantic."""
    error_type = error["type"]
    message = str(error["msg"])
    ctx = dict(error.get("ctx") or {})

    if error_type == "string_too_short" and ctx.get("min_length") == 1:
        return REQUIRED_MESSAGE

    if error_type == "value_error":
        # El validador de email lanza texto en inglés; el resto son nuestros validadores.
        if message.startswith(EMAIL_PREFIX):
            return "Introduce un email válido."
        return message.removeprefix("Value error, ")

    template = _VALIDATION_MESSAGES.get(error_type)
    if template is None:
        return message

    if "expected" in ctx:
        ctx["expected"] = str(ctx["expected"]).replace(" or ", " o ")

    try:
        return template.format(**ctx)
    except (KeyError, IndexError):
        # Si ctx no trae lo esperado, es mejor el texto original que un fallo.
        return message


def translate_http_detail(detail: str) -> str:
    """Traduce los detalles HTTP por defecto; el resto se devuelve sin cambios."""
    return _HTTP_DETAILS.get(detail, detail)
