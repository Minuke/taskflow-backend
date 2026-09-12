from datetime import date, datetime
from decimal import Decimal

from pydantic import ConfigDict, Field, field_validator

from app.core.dates import today_utc
from app.models.task import Priority
from app.schemas.base import CamelModel


class TaskBase(CamelModel):
    title: str = Field(min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    priority: Priority = Priority.MEDIUM
    estimated_hours: Decimal = Field(ge=0, max_digits=5, decimal_places=2)
    due_date: date | None = None
    category_id: int | None = None


class TaskCreate(TaskBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Estudiar FastAPI",
                    "description": "Repasar dependency injection y validación con Pydantic.",
                    "priority": "medium",
                    "estimatedHours": 2.5,
                    "dueDate": "2026-12-31",
                }
            ]
        }
    )

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value: date | None) -> date | None:
        if value is not None and value < today_utc():
            raise ValueError("La fecha límite no puede ser anterior a hoy.")
        return value

class TaskUpdate(TaskBase):
    """Misma forma que TaskCreate, pero sin la validación de fecha aquí:
    en edición, esa regla depende del valor anterior guardado en la base
    de datos, algo que el esquema no puede conocer por sí solo — se aplica
    directamente en el endpoint (ver app/api/tasks.py)."""


class TaskRead(TaskBase):
    id: int
    completed: bool
    image: str | None
    created_at: datetime
    updated_at: datetime

class TaskPage(CamelModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    total_pages: int