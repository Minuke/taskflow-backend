from app.schemas.base import CamelModel


class FieldError(CamelModel):
    field: str
    message: str


class ErrorResponse(CamelModel):
    detail: str
    errors: list[FieldError] | None = None