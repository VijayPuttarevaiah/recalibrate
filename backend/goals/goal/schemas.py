from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from domain.goal_category import GoalCategory


class GoalCreate(BaseModel):
    user_id: int
    goal: str
    category: GoalCategory
    start_date: date
    end_date: date
    notes: str | None = None


class TaskResponse(BaseModel):
    id: int
    goal_id: int
    title: str
    description: str | None = None
    due_date: date
    status: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GoalResumeRequest(BaseModel):
    mode: Literal["keep_original", "new_end_date"]
    new_end_date: date | None = None
    original_end_date: date | None = None

    @model_validator(mode="after")
    def validate_new_end_date(self):
        if self.mode == "new_end_date" and self.new_end_date is None:
            raise ValueError("new_end_date is required when mode is 'new_end_date'")
        if (
            self.mode == "new_end_date"
            and self.new_end_date is not None
            and self.new_end_date <= date.today()
        ):
            raise ValueError("new_end_date must be a future date")
        return self


class GoalResponse(BaseModel):
    id: int
    title: str
    category: str | None = None
    notes: str | None = None
    start_date: date
    end_date: date
    status: str
    paused_at: datetime | None = None
    task_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class GoalWithTasksResponse(BaseModel):
    id: int
    title: str
    category: str | None = None
    notes: str | None = None
    start_date: date
    end_date: date
    status: str
    paused_at: datetime | None = None
    task_count: int = 0
    tasks: list[TaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
