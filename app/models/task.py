from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    priority: Mapped[Priority] = mapped_column(
        SqlEnum(
            Priority,
            name="priority_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=Priority.MEDIUM,
    )
    estimated_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    image: Mapped[Optional[str]] = mapped_column(String(255))
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="tasks")
    category: Mapped[Optional["Category"]] = relationship(back_populates="tasks")