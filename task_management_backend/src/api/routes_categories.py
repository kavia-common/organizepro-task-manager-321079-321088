"""Category routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db_session
from .models import Category
from .schemas import CategoryCreate, CategoryOut, CategoryUpdate, ApiMessage

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut], summary="List categories")
def list_categories(db: Session = Depends(get_db_session)):
    """
    List all categories.

    Returns:
        A list of categories.
    """
    categories = db.execute(select(Category).order_by(Category.name.asc())).scalars().all()
    return categories


@router.post(
    "",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db_session)):
    """
    Create a new category.

    Args:
        payload: CategoryCreate data.
    """
    category = Category(name=payload.name.strip(), description=payload.description)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    db.refresh(category)
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryOut,
    summary="Update category",
)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db_session)):
    """
    Update an existing category.

    Args:
        category_id: The category to update.
        payload: Partial update fields.
    """
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if payload.name is not None:
        category.name = payload.name.strip()
    if payload.description is not None:
        category.description = payload.description

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Category name already exists")
    db.refresh(category)
    return category


@router.delete(
    "/{category_id}",
    response_model=ApiMessage,
    summary="Delete category",
)
def delete_category(category_id: int, db: Session = Depends(get_db_session)):
    """
    Delete a category.

    Note: Tasks in this category will have category_id set to NULL due to FK ondelete=SET NULL.
    """
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()
    return ApiMessage(message="Category deleted")
