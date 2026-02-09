from domain.goal_category import GoalCategory
from schemas.goal_schemas import GoalCategoryDetectResponse
from utils.groq_client import GroqClient
from utils.logging_config import LogManager

logger = LogManager.get_logger()


class GoalCategoryService:
    def __init__(self, client: GroqClient | None = None):
        self.client = client or GroqClient()

    def analyze_goal(
        self,
        goal_text: str,
        start_date=None,
        end_date=None,
        note: str | None = None,
    ) -> GoalCategoryDetectResponse:
        categories = GoalCategory.values()
        result = self.client.analyze_goal(goal_text, categories, start_date=start_date, end_date=end_date, note=note)
        if not result:
            logger.warning("LLM analysis unavailable; requesting more details")
            return GoalCategoryDetectResponse(
                status="needs_more_info",
                category=None,
                follow_up_questions=["Please add more detail about your goal and timeline."],
            )

        is_sufficient = bool(result.get("is_sufficient"))
        category = GoalCategory.from_raw(result.get("category"))
        follow_up_questions = result.get("follow_up_questions") or []

        if not is_sufficient or not category:
            logger.info("Goal is too vague or category missing")
            if not follow_up_questions:
                follow_up_questions = ["Please add more detail about your goal and timeline."]
            return GoalCategoryDetectResponse(
                status="needs_more_info",
                category=category,
                follow_up_questions=follow_up_questions,
            )

        logger.info(f"LLM detected category: {category.value}")
        return GoalCategoryDetectResponse(
            status="accepted",
            category=category,
            follow_up_questions=[],
        )

