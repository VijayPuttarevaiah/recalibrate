"""Check whether a goal needs replanning."""
from datetime import date
from sqlalchemy.orm import Session
from goals.models.task_models import Task
from replan.detect.service import detect_missed_tasks

DEFAULT_REPLAN_THRESHOLD = 3


def check_goal_needs_replan(db: Session, goal_id: int, threshold: int = DEFAULT_REPLAN_THRESHOLD) -> dict:
    """
    Quick check: does this goal need replanning?
    Returns status info without triggering a replan.

    threshold: minimum missed tasks before suggesting a replan (default 3)
    """
    missed = detect_missed_tasks(db, goal_id)
    total_past = (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.due_date < date.today())
        .count()
    )
    completed = (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.status == "completed")
        .count()
    )

    needs_replan = len(missed) >= threshold

    return {
        "goal_id": goal_id,
        "missed_count": len(missed),
        "completed_count": completed,
        "total_past_tasks": total_past,
        "threshold": threshold,
        "needs_replan": needs_replan,
    }
