from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_owned_category_or_404, get_owned_task_or_404
from app.core.dates import today_utc
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from fastapi import Query
from sqlalchemy import select
from app.schemas.task_query import DueFilter, PriorityFilter, SortField, SortOrder, StatusFilter
from app.services.task_query_service import build_order_by, build_task_conditions

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _ensure_category_belongs_to_user(db: Session, category_id: int | None, user_id: int) -> None:
    if category_id is not None:
        get_owned_category_or_404(db, category_id, user_id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    _ensure_category_belongs_to_user(db, payload.category_id, current_user.id)

    task = Task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        estimated_hours=payload.estimated_hours,
        due_date=payload.due_date,
        category_id=payload.category_id,
        user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return get_owned_task_or_404(db, task_id, current_user.id)


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task_or_404(db, task_id, current_user.id)
    _ensure_category_belongs_to_user(db, payload.category_id, current_user.id)

    due_date_changed = payload.due_date != task.due_date
    if due_date_changed and payload.due_date is not None and payload.due_date < today_utc():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha límite no puede ser anterior a hoy.",
        )

    task.title = payload.title
    task.description = payload.description
    task.priority = payload.priority
    task.estimated_hours = payload.estimated_hours
    task.due_date = payload.due_date
    task.category_id = payload.category_id

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.patch("/{task_id}/complete", response_model=TaskRead)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task_or_404(db, task_id, current_user.id)

    if not task.completed:
        task.completed = True
        db.add(task)
        db.commit()
        db.refresh(task)

    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = get_owned_task_or_404(db, task_id, current_user.id)
    db.delete(task)
    db.commit()

@router.get("", response_model=list[TaskRead])
def list_tasks(
    search: str | None = Query(default=None),
    status_filter: StatusFilter = Query(default=StatusFilter.ALL, alias="status"),
    priority_filter: PriorityFilter = Query(default=PriorityFilter.ALL, alias="priority"),
    category_id: int | None = Query(default=None),
    due: DueFilter = Query(default=DueFilter.ALL),
    sort_by: SortField = Query(default=SortField.UPDATED_AT),
    order: SortOrder = Query(default=SortOrder.DESC),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    conditions = build_task_conditions(
        user_id=current_user.id,
        search=search,
        status_filter=status_filter,
        priority_filter=priority_filter,
        category_id=category_id,
        due=due,
    )
    order_by_clauses = build_order_by(sort_by, order)

    stmt = select(Task).where(*conditions).order_by(*order_by_clauses)
    return list(db.scalars(stmt).all())