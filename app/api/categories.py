from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_category_or_404
from app.db.session import get_db
from app.models.category import Category
from app.models.task import Task
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryListItem, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryListItem])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CategoryListItem]:
    task_counts = (
        select(Task.category_id, func.count(Task.id).label("task_count"))
        .group_by(Task.category_id)
        .subquery()
    )

    stmt = (
        select(Category, func.coalesce(task_counts.c.task_count, 0))
        .outerjoin(task_counts, task_counts.c.category_id == Category.id)
        .where(Category.user_id == current_user.id)
        .order_by(Category.name)
    )

    rows = db.execute(stmt).all()

    return [
        CategoryListItem(
            id=category.id,
            name=category.name,
            description=category.description,
            task_count=task_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
        for category, task_count in rows
    ]


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = Category(name=payload.name, description=payload.description, user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    return get_owned_category_or_404(db, category_id, current_user.id)


@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = get_owned_category_or_404(db, category_id, current_user.id)
    category.name = payload.name
    category.description = payload.description
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    category = get_owned_category_or_404(db, category_id, current_user.id)
    db.delete(category)
    db.commit()