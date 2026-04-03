# routes/task_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from goals.models.task_models import Task
from goals.models.goal_models import Goal
from core.db_session import get_db
from auth.utils.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

from domain.goal_status import TASK_STATUSES as VALID_STATUSES


class TaskStatusUpdate(BaseModel):
    status: str


class TaskBatchUpdate(BaseModel):
    task_ids: list[int]
    status: str


class TaskNotesUpdate(BaseModel):
    notes: str


# ── Helper: verify task belongs to user ──


def _get_user_task(db: Session, task_id: int, user_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    goal = (
        db.query(Goal)
        .filter(
            Goal.id == task.goal_id,
            Goal.user_id == user_id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=403, detail="Not your task")

    return task


@router.patch("/{task_id}/status")
def update_task_status(
    task_id: int,
    body: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a single task as completed/missed/skipped."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )

    task = _get_user_task(db, task_id, current_user["user_id"])
    task.status = body.status
    db.commit()
    return {"task_id": task.id, "new_status": task.status}


@router.patch("/{task_id}/notes")
def update_task_notes(
    task_id: int,
    body: TaskNotesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add or update notes on a task."""
    task = _get_user_task(db, task_id, current_user["user_id"])
    task.notes = body.notes.strip()
    db.commit()
    db.refresh(task)
    return {
        "task_id": task.id,
        "notes": task.notes,
    }


@router.get("/{task_id}")
def get_task_detail(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full task detail including notes."""
    task = _get_user_task(db, task_id, current_user["user_id"])
    detail = {
        "id": task.id,
        "goal_id": task.goal_id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date,
        "status": task.status,
        "notes": task.notes,
    }
    return detail


@router.patch("/batch-status")
def batch_update_tasks(
    body: TaskBatchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark multiple tasks at once."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )

    updated = []
    for task_id in body.task_ids:
        try:
            task = _get_user_task(db, task_id, current_user["user_id"])
            task.status = body.status
            updated.append(task_id)
        except HTTPException:
            continue

    db.commit()
    return {"updated_task_ids": updated, "new_status": body.status}
