from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from goals.goal.schemas import GoalCreate, GoalResponse, GoalWithTasksResponse, GoalResumeRequest
from goals.goal.service import create_goal_with_tasks, get_user_goals, get_goal_tasks, pause_goal, resume_goal
from core.db_session import get_db
from auth.utils.auth import get_current_user

router = APIRouter(prefix="/goals", tags=["goals"])


def _user_id(current_user: dict) -> int:
    return current_user["user_id"]


@router.post("/create")
def create_goal_api(request: GoalCreate, db: Session = Depends(get_db)):
    goal = create_goal_with_tasks(db, request)
    return {
        "message": "Goal created successfully",
        "goal_id": goal.id,
    }


@router.get("/", response_model=list[GoalResponse])
def get_goals_api(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_goals(db, _user_id(current_user))


@router.get("/{goal_id}/tasks", response_model=GoalWithTasksResponse)
def get_goal_tasks_api(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_goal_tasks(db, _user_id(current_user), goal_id)


@router.patch("/{goal_id}/pause")
def pause_goal_api(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return pause_goal(db, user_id=_user_id(current_user), goal_id=goal_id)


@router.patch("/{goal_id}/resume")
def resume_goal_api(
    goal_id: int,
    body: GoalResumeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return resume_goal(db, user_id=_user_id(current_user), goal_id=goal_id, body=body)
