from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_category_or_404, get_owned_task_or_404
from app.core.dates import today_utc
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

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