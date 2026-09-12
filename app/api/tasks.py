from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_owned_category_or_404, get_owned_task_or_404
from app.core.dates import today_utc
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPage, TaskRead, TaskUpdate
from fastapi import Query
from sqlalchemy import select, func
from app.schemas.task_query import DueFilter, PriorityFilter, SortField, SortOrder, StatusFilter
from app.services.task_query_service import build_order_by, build_task_conditions
import io
import uuid
from pathlib import Path
from fastapi import File, UploadFile
from PIL import Image, UnidentifiedImageError
from app.core.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _delete_task_image_file(image_url: str | None) -> None:
    if not image_url:
        return
    filename = Path(image_url).name
    (UPLOAD_DIR / filename).unlink(missing_ok=True)


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

@router.get("", response_model=TaskPage)
def list_tasks(
    search: str | None = Query(default=None),
    status_filter: StatusFilter = Query(default=StatusFilter.ALL, alias="status"),
    priority_filter: PriorityFilter = Query(default=PriorityFilter.ALL, alias="priority"),
    category_id: int | None = Query(default=None),
    due: DueFilter = Query(default=DueFilter.ALL),
    sort_by: SortField = Query(default=SortField.UPDATED_AT),
    order: SortOrder = Query(default=SortOrder.DESC),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskPage:
    conditions = build_task_conditions(
        user_id=current_user.id,
        search=search,
        status_filter=status_filter,
        priority_filter=priority_filter,
        category_id=category_id,
        due=due,
    )
    order_by_clauses = build_order_by(sort_by, order)

    total = db.scalar(select(func.count()).select_from(Task).where(*conditions)) or 0

    items_stmt = (
        select(Task)
        .where(*conditions)
        .order_by(*order_by_clauses)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(items_stmt).all())

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return TaskPage(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post("/{task_id}/image", response_model=TaskRead)
def upload_task_image(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task_or_404(db, task_id, current_user.id)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Formato no permitido. Sube una imagen JPEG, PNG o WEBP.",
        )

    contents = file.file.read()

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"La imagen no puede superar los {settings.max_upload_size_mb} MB.",
        )

    try:
        buffer = io.BytesIO(contents)
        Image.open(buffer).verify()
        buffer.seek(0)
        image_format = Image.open(buffer).format
    except UnidentifiedImageError:
        image_format = None

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo no es una imagen válida.",
        )

    _delete_task_image_file(task.image)

    filename = f"{uuid.uuid4().hex}{ALLOWED_IMAGE_FORMATS[image_format]}"
    (UPLOAD_DIR / filename).write_bytes(contents)

    task.image = f"/media/tasks/{filename}"
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}/image", response_model=TaskRead)
def delete_task_image(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = get_owned_task_or_404(db, task_id, current_user.id)

    _delete_task_image_file(task.image)
    task.image = None

    db.add(task)
    db.commit()
    db.refresh(task)
    return task