# routes/task_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from models.task_models import Task
from models.goal_models import Goal
from utils.db_session import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

VALID_STATUSES = {"pending", "completed", "missed", "skipped"}


class TaskStatusUpdate(BaseModel):
    status: str  # "completed", "missed", "skipped"


class TaskBatchUpdate(BaseModel):
    task_ids: list[int]
    status: str


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

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Verify the task's goal belongs to this user
    goal = db.query(Goal).filter(
        Goal.id == task.goal_id,
        Goal.user_id == current_user["user_id"],
    ).first()
    if not goal:
        raise HTTPException(status_code=403, detail="Not your task")

    task.status = body.status
    db.commit()
    return {"task_id": task.id, "new_status": task.status}


@router.patch("/batch-status")
def batch_update_tasks(
    body: TaskBatchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark multiple tasks at once (e.g., bulk complete)."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )

    updated = []
    for task_id in body.task_ids:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            continue
        goal = db.query(Goal).filter(
            Goal.id == task.goal_id,
            Goal.user_id == current_user["user_id"],
        ).first()
        if not goal:
            continue
        task.status = body.status
        updated.append(task_id)

    db.commit()
    return {"updated_task_ids": updated, "new_status": body.status}