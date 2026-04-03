"""Detection functions for missed tasks."""

from datetime import date
from sqlalchemy.orm import Session
from goals.models.task_models import Task


def detect_missed_tasks(db: Session, goal_id: int) -> list[Task]:
    """Find all pending tasks whose due_date has passed."""
    today = date.today()
    return (
        db.query(Task)
        .filter(
            Task.goal_id == goal_id,
            Task.status == "pending",
            Task.due_date < today,
        )
        .order_by(Task.due_date)
        .all()
    )
