from fastapi import APIRouter
from schemas.goal_schemas import GoalCategoryDetectRequest, GoalCategoryDetectResponse
from services.goal_category_service import GoalCategoryService
from utils.logging_config import LogManager

logger = LogManager.get_logger()

router = APIRouter()


@router.post("/goals/category", response_model=GoalCategoryDetectResponse)
def detect_goal_category(payload: GoalCategoryDetectRequest):
    logger.info("goal category request received")
    category_service = GoalCategoryService()
    analysis = category_service.analyze_goal(
        payload.goal_text,
        start_date=payload.start_date,
        end_date=payload.end_date,
        note=payload.note,
    )

    return analysis


