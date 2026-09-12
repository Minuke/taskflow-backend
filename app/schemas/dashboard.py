from app.schemas.base import CamelModel
from app.schemas.task import TaskRead


class DashboardSummary(CamelModel):
    total: int
    completed: int
    pending: int
    high_priority_count: int
    due_today: int


class DashboardResponse(CamelModel):
    summary: DashboardSummary
    upcoming: list[TaskRead]
    priority: list[TaskRead]
    recent: list[TaskRead]