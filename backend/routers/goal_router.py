from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from exceptions.llm_exceptions import LLMClientError
from schemas.goal_schemas import GoalCategoryDetectRequest, GoalCategoryDetectResponse
from schemas.goal_schemas import GoalCreate
from services.goal_category_service import GoalCategoryService
from services.goal_service import create_goal_with_tasks
from utils.db_session import get_db
from utils.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()


@router.post("/goals/category", response_model=GoalCategoryDetectResponse)
def detect_goal_category(
    payload: GoalCategoryDetectRequest,
    db: Session = Depends(get_db),
):
    logger.info("goal category request received")
    category_service = GoalCategoryService()
    try:
        analysis = category_service.analyze_goal(
            payload.goal_text,
            start_date=payload.start_date,
            end_date=payload.end_date,
            note=payload.note,
        )
    except LLMClientError as exc:
        logger.warning(f"goal category analysis failed: {exc.error_code}")
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.to_http_detail(),
        ) from exc

    if analysis.status == "accepted" and analysis.category is not None:
        if payload.user_id is None:
            return GoalCategoryDetectResponse(
                status="needs_more_info",
                category=analysis.category,
                follow_up_questions=[
                    "Please provide user_id to create the goal.",
                ],
            )

        goal_request = GoalCreate(
            user_id=payload.user_id,
            goal=payload.goal_text,
            category=analysis.category,
            start_date=payload.start_date,
            end_date=payload.end_date,
            notes=payload.note,
        )
        created_goal = create_goal_with_tasks(db, goal_request)
        return GoalCategoryDetectResponse(
            status="accepted",
            category=analysis.category,
            follow_up_questions=[],
            goal_id=created_goal.id,
            message="Category detected and goal created successfully",
        )

    return analysis


