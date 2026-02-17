from pydantic import BaseModel
from datetime import date

class GoalCreate(BaseModel):
    user_id: int
    goal: str
    category: str
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

    class Config:
        from_attributes = True


class GoalResponse(BaseModel):
    id: int
    title: str
    category: str | None = None
    notes: str | None = None
    start_date: date
    end_date: date
    status: str
    task_count: int = 0

    class Config:
        from_attributes = True


class GoalWithTasksResponse(GoalResponse):
    tasks: list[TaskResponse] = []
