import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.error import ErrorResponse, FieldError

logger = logging.getLogger("taskflow")


def _field_name_from_loc(loc: tuple) -> str:
    parts = [str(part) for part in loc if part not in ("body", "query", "path")]
    return ".".join(parts) if parts else "unknown"


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        FieldError(field=_field_name_from_loc(error["loc"]), message=error["msg"])
        for error in exc.errors()
    ]
    body = ErrorResponse(detail="Los datos enviados no son válidos.", errors=errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body.model_dump(by_alias=True),
    )


def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    body = ErrorResponse(detail=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(by_alias=True),
        headers=exc.headers,
    )


def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Violación de integridad en la base de datos: %s", exc)
    body = ErrorResponse(
        detail="Ya existe un registro con esos datos, o hace referencia a algo que no existe."
    )
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=body.model_dump(by_alias=True))


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado procesando %s %s", request.method, request.url.path)
    body = ErrorResponse(detail="Ha ocurrido un error inesperado. Inténtalo de nuevo más tarde.")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body.model_dump(by_alias=True)
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)