"""Pydantic models (schemas) for API I/O."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, Field

from .models import TaskPriority


class ApiMessage(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Human-readable message")


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=80, description="Category name (unique)")
    description: Optional[str] = Field(None, max_length=2000, description="Optional category description")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80, description="Updated category name")
    description: Optional[str] = Field(None, max_length=2000, description="Updated category description")


class CategoryOut(CategoryBase):
    id: int = Field(..., description="Category id")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    due_date: Optional[date] = Field(None, description="Due date (YYYY-MM-DD)")
    priority: TaskPriority = Field(TaskPriority.medium, description="Task priority")
    category_id: Optional[int] = Field(None, description="Associated category id (nullable)")


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated title")
    description: Optional[str] = Field(None, max_length=5000, description="Updated description")
    due_date: Optional[date] = Field(None, description="Updated due date")
    priority: Optional[TaskPriority] = Field(None, description="Updated priority")
    category_id: Optional[int] = Field(None, description="Updated category id (nullable)")
    is_completed: Optional[bool] = Field(None, description="Mark complete/incomplete")


class TaskOut(TaskBase):
    id: int = Field(..., description="Task id")
    is_completed: bool = Field(..., description="Completion flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True


class TaskListOut(BaseModel):
    items: List[TaskOut] = Field(..., description="Tasks in current page")
    total: int = Field(..., ge=0, description="Total tasks matching the filter")
    limit: int = Field(..., ge=1, le=200, description="Page size")
    offset: int = Field(..., ge=0, description="Offset into the full result set")


TaskStatusFilter = Literal["all", "active", "completed"]
TaskSortBy = Literal["created_at", "due_date", "priority", "title"]
SortOrder = Literal["asc", "desc"]
