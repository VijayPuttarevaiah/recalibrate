from datetime import date
from pydantic import BaseModel, Field, ConfigDict
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


class GoalResponse(BaseModel):
    id: int
    title: str
    category: str | None = None
    notes: str | None = None
    start_date: date
    end_date: date
    status: str
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
    task_count: int = 0
    tasks: list[TaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
