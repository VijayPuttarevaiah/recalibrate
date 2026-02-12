from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.goal_schemas import GoalCreate
from services.goal_service import create_goal_with_tasks
from utils.db_session import get_db

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/goal-create")
def create_goal_api(request: GoalCreate, db: Session = Depends(get_db)):
    goal = create_goal_with_tasks(
        db,request
    )

    return {
        "message": "Goal created successfully",
        "goal_id": goal.id
    }
