# routes/replan_routes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from goals.models.goal_adjustment_models import GoalAdjustment
from replan.routes.schemas import (
    ReplanCheckResponse,
    ReplanResponse,
    AdjustmentHistoryItem,
)
from replan.check.service import check_goal_needs_replan
from replan.goal.service import replan_goal
from core.db_session import get_db
from auth.utils.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["replanning"])


def _user_id(current_user: dict) -> int:
    return current_user["user_id"]


# ── 1. Check if a goal needs replanning (lightweight, no LLM call) ──


@router.get("/{goal_id}/replan/check", response_model=ReplanCheckResponse)
def check_replan_status(
    goal_id: int,
    threshold: int = Query(default=3, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Quick check: should this goal be replanned?
    Returns missed task count and a boolean recommendation.
    No LLM calls — safe to poll frequently.
    """
    return check_goal_needs_replan(
        db,
        goal_id,
        threshold=threshold,
    )


# ── 2. Trigger a replan (heavy: web research + LLM calls) ──


@router.post("/{goal_id}/replan", response_model=ReplanResponse)
def trigger_replan(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Replan a goal:
    - Marks overdue tasks as "missed"
    - Deletes all future pending tasks
    - Regenerates from today → end_date using progress context
    - Returns a trade-off explanation
    """
    return replan_goal(
        db,
        _user_id(current_user),
        goal_id,
    )


# ── 3. View past adjustments ──


@router.get(
    "/{goal_id}/replan/history",
    response_model=list[AdjustmentHistoryItem],
)
def get_adjustment_history(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the history of all plan adjustments for a goal."""
    adjustments = (
        db.query(GoalAdjustment)
        .filter(GoalAdjustment.goal_id == goal_id)
        .order_by(GoalAdjustment.created_at.desc())
        .all()
    )
    return [
        AdjustmentHistoryItem(
            id=a.id,
            missed_task_count=a.missed_task_count,
            completed_task_count=a.completed_task_count,
            tasks_deleted=a.tasks_deleted,
            tasks_created=a.tasks_created,
            explanation=a.explanation,
            created_at=a.created_at.isoformat(),
        )
        for a in adjustments
    ]
