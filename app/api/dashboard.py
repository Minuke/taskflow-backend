from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dates import today_utc
from app.db.session import get_db
from app.models.task import Priority, Task
from app.models.user import User
from app.schemas.dashboard import DashboardResponse, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DASHBOARD_LIST_LIMIT = 4


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    today = today_utc()

    summary_stmt = select(
        func.count().label("total"),
        func.count().filter(Task.completed.is_(True)).label("completed"),
        func.count().filter(Task.completed.is_(False)).label("pending"),
        func.count().filter(Task.priority == Priority.HIGH).label("high_priority_count"),
        func.count()
        .filter(and_(Task.completed.is_(False), Task.due_date == today))
        .label("due_today"),
    ).where(Task.user_id == current_user.id)

    summary_row = db.execute(summary_stmt).one()
    summary = DashboardSummary(
        total=summary_row.total,
        completed=summary_row.completed,
        pending=summary_row.pending,
        high_priority_count=summary_row.high_priority_count,
        due_today=summary_row.due_today,
    )

    upcoming_stmt = (
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.completed.is_(False),
            Task.due_date.is_not(None),
        )
        .order_by(Task.due_date.asc())
        .limit(DASHBOARD_LIST_LIMIT)
    )
    upcoming = list(db.scalars(upcoming_stmt).all())

    priority_stmt = (
        select(Task)
        .where(
            Task.user_id == current_user.id,
            Task.completed.is_(False),
            Task.priority == Priority.HIGH,
        )
        .order_by(Task.id.asc())
        .limit(DASHBOARD_LIST_LIMIT)
    )
    priority = list(db.scalars(priority_stmt).all())

    recent_stmt = (
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.updated_at.desc())
        .limit(DASHBOARD_LIST_LIMIT)
    )
    recent = list(db.scalars(recent_stmt).all())

    return DashboardResponse(summary=summary, upcoming=upcoming, priority=priority, recent=recent)