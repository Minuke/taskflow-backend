from datetime import datetime

from pydantic import Field

from app.schemas.base import CamelModel


class CategoryBase(CamelModel):
    name: str = Field(min_length=2, max_length=40)
    description: str | None = Field(default=None, max_length=200)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime


class CategoryListItem(CategoryRead):
    task_count: int