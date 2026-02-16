"""Task routes."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import get_db_session
from .models import Task, Category, TaskPriority
from .schemas import (
    TaskCreate,
    TaskOut,
    TaskUpdate,
    TaskListOut,
    TaskStatusFilter,
    TaskSortBy,
    SortOrder,
    ApiMessage,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _apply_status_filter(stmt, status_filter: TaskStatusFilter):
    if status_filter == "active":
        return stmt.where(Task.is_completed.is_(False))
    if status_filter == "completed":
        return stmt.where(Task.is_completed.is_(True))
    return stmt


def _apply_category_filter(stmt, category_id: Optional[int]):
    if category_id is None:
        return stmt
    return stmt.where(Task.category_id == category_id)


def _apply_text_search(stmt, q: Optional[str]):
    if not q:
        return stmt
    like = f"%{q.strip()}%"
    return stmt.where((Task.title.ilike(like)) | (Task.description.ilike(like)))


def _apply_sort(stmt, sort_by: TaskSortBy, order: SortOrder):
    col = {
        "created_at": Task.created_at,
        "due_date": Task.due_date,
        "priority": Task.priority,
        "title": Task.title,
    }[sort_by]
    return stmt.order_by(col.desc() if order == "desc" else col.asc())


@router.get("", response_model=TaskListOut, summary="List tasks (filter/sort/paginate)")
def list_tasks(
    db: Session = Depends(get_db_session),
    status_filter: TaskStatusFilter = Query("all", alias="status", description="Filter by completion status"),
    category_id: Optional[int] = Query(None, description="Filter by category id"),
    q: Optional[str] = Query(None, description="Text search across title/description"),
    due_from: Optional[date] = Query(None, description="Filter due_date >= due_from"),
    due_to: Optional[date] = Query(None, description="Filter due_date <= due_to"),
    sort_by: TaskSortBy = Query("created_at", description="Field to sort by"),
    order: SortOrder = Query("desc", description="Sort order"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
):
    """
    List tasks with common filters.

    Returns:
        Paginated list of tasks.
    """
    stmt = select(Task)
    stmt = _apply_status_filter(stmt, status_filter)
    stmt = _apply_category_filter(stmt, category_id)
    stmt = _apply_text_search(stmt, q)
    if due_from is not None:
        stmt = stmt.where(Task.due_date.is_not(None)).where(Task.due_date >= due_from)
    if due_to is not None:
        stmt = stmt.where(Task.due_date.is_not(None)).where(Task.due_date <= due_to)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    stmt = _apply_sort(stmt, sort_by, order).limit(limit).offset(offset)
    items = db.execute(stmt).scalars().all()

    return TaskListOut(items=items, total=total, limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TaskOut, summary="Get task")
def get_task(task_id: int, db: Session = Depends(get_db_session)):
    """
    Get a task by id.
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED, summary="Create task")
def create_task(payload: TaskCreate, db: Session = Depends(get_db_session)):
    """
    Create a task.

    Validates category_id if provided.
    """
    if payload.category_id is not None:
        category = db.get(Category, payload.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category_id")

    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        due_date=payload.due_date,
        priority=payload.priority or TaskPriority.medium,
        category_id=payload.category_id,
        is_completed=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskOut, summary="Update task")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db_session)):
    """
    Update a task (supports partial updates).
    """
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.category_id is not None:
        if payload.category_id is not None:
            category = db.get(Category, payload.category_id)
            if not category:
                raise HTTPException(status_code=400, detail="Invalid category_id")

    if payload.title is not None:
        task.title = payload.title.strip()
    if payload.description is not None:
        task.description = payload.description
    if payload.due_date is not None or payload.due_date is None:
        # If provided explicitly as null, allow clearing. (Pydantic sends None when set)
        if "due_date" in payload.model_fields_set:
            task.due_date = payload.due_date
    if payload.priority is not None:
        task.priority = payload.priority
    if "category_id" in payload.model_fields_set:
        task.category_id = payload.category_id
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed

    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/complete", response_model=TaskOut, summary="Mark task complete")
def mark_complete(task_id: int, db: Session = Depends(get_db_session)):
    """Convenience endpoint to mark a task completed."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = True
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/reopen", response_model=TaskOut, summary="Reopen task")
def reopen_task(task_id: int, db: Session = Depends(get_db_session)):
    """Convenience endpoint to mark a task active again."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = False
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", response_model=ApiMessage, summary="Delete task")
def delete_task(task_id: int, db: Session = Depends(get_db_session)):
    """Delete a task."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return ApiMessage(message="Task deleted")
