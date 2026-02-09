from services.goal_category_service import GoalCategoryService
from domain.goal_category import GoalCategory


class FakeGroqClient:
    def __init__(self, response: dict | None):
        self.response = response

    def analyze_goal(
        self,
        goal_text: str,
        categories: list[str],
        start_date=None,
        end_date=None,
        note: str | None = None,
    ) -> dict | None:
        return self.response


def test_analyze_goal_accepts_when_sufficient_and_category():
    service = GoalCategoryService(
        client=FakeGroqClient({"is_sufficient": True, "category": "fitness", "follow_up_questions": []})
    )
    result = service.analyze_goal("Run a half marathon")
    assert result.status == "accepted"
    assert result.category == GoalCategory.FITNESS


def test_analyze_goal_requests_more_info_when_vague():
    service = GoalCategoryService(
        client=FakeGroqClient({"is_sufficient": False, "category": None, "follow_up_questions": ["When?"]})
    )
    result = service.analyze_goal("Get fit")
    assert result.status == "needs_more_info"
    assert result.follow_up_questions == ["When?"]
