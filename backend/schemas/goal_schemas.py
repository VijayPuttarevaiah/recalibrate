from pydantic import BaseModel
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date
from domain.goal_category import GoalCategory


class GoalCategoryDetectRequest(BaseModel):
    goal_text: str
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None


class GoalCategoryDetectResponse(BaseModel):
    status: Literal["accepted", "needs_more_info"]
    category: GoalCategory | None = None
    follow_up_questions: list[str] = Field(default_factory=list)


class GoalCreate(BaseModel):
    user_id: int
    goal: str
    category: str
    start_date: date
    end_date: date
    notes: str | None = None
