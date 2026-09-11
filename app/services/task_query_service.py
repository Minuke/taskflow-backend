from sqlalchemy import ColumnElement, or_

from app.core.dates import today_utc
from app.models.task import Priority, Task
from app.schemas.task_query import DueFilter, PriorityFilter, SortField, SortOrder, StatusFilter

SORT_COLUMNS = {
    SortField.TITLE: Task.title,
    SortField.PRIORITY: Task.priority,
    SortField.DUE_DATE: Task.due_date,
    SortField.CREATED_AT: Task.created_at,
    SortField.UPDATED_AT: Task.updated_at,
}


def build_task_conditions(
    user_id: int,
    search: str | None,
    status_filter: StatusFilter,
    priority_filter: PriorityFilter,
    category_id: int | None,
    due: DueFilter,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Task.user_id == user_id]

    if search:
        term = f"%{search}%"
        conditions.append(or_(Task.title.ilike(term), Task.description.ilike(term)))

    if status_filter == StatusFilter.PENDING:
        conditions.append(Task.completed.is_(False))
    elif status_filter == StatusFilter.COMPLETED:
        conditions.append(Task.completed.is_(True))

    if priority_filter != PriorityFilter.ALL:
        conditions.append(Task.priority == Priority(priority_filter.value))

    if category_id is not None:
        conditions.append(Task.category_id == category_id)

    today = today_utc()
    if due == DueFilter.OVERDUE:
        conditions.append(Task.due_date.is_not(None))
        conditions.append(Task.due_date < today)
        conditions.append(Task.completed.is_(False))
    elif due == DueFilter.TODAY:
        conditions.append(Task.due_date == today)
    elif due == DueFilter.UPCOMING:
        conditions.append(Task.due_date.is_not(None))
        conditions.append(Task.due_date > today)
    elif due == DueFilter.NO_DATE:
        conditions.append(Task.due_date.is_(None))

    return conditions


def build_order_by(sort_by: SortField, order: SortOrder) -> list:
    column = SORT_COLUMNS[sort_by]
    direction = column.asc() if order == SortOrder.ASC else column.desc()

    if sort_by == SortField.DUE_DATE:
        direction = direction.nulls_last()

    # Desempate: siempre por prioridad descendente (High > Medium > Low),
    # sea cual sea el criterio principal elegido. Ver explicación más abajo.
    return [direction, Task.priority.desc()]