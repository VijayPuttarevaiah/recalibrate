from domain.goal_category import GoalCategory
from schemas.goal_schemas import GoalCategoryDetectResponse
from services.goal_category_service import GoalCategoryService


def test_goal_category_endpoint_returns_category(client, monkeypatch):
    def fake_analyze(self, goal_text: str):
        return GoalCategoryDetectResponse(
            status="accepted",
            category=GoalCategory.FITNESS,
            follow_up_questions=[],
        )

    monkeypatch.setattr(GoalCategoryService, "analyze_goal", fake_analyze)

    response = client.post(
        "/goals/category",
        json={"goal_text": "Lose 2kg in 20 days", "start_date": "2026-02-08", "end_date": "2026-02-27"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["category"] == GoalCategory.FITNESS.value
