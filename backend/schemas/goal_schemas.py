from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from domain.goal_category import GoalCategory


class GoalCreate(BaseModel):
    user_id: int
    goal: str
    category: GoalCategory
    start_date: date
    end_date: date
    notes: str | None = None


class GoalCategoryDetectRequest(BaseModel):
    goal_text: str
    start_date: date
    end_date: date
    note: str | None = None
    user_id: int | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be greater than start_date")
        return self


class GoalCategoryDetectResponse(BaseModel):
    status: Literal["accepted", "needs_more_info"]
    category: GoalCategory | None = None
    follow_up_questions: list[str] = Field(default_factory=list)
    goal_id: int | None = None
    message: str | None = None
