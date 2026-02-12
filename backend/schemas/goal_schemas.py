from pydantic import BaseModel
from datetime import date

class GoalCreate(BaseModel):
    user_id: int
    goal: str
    category: str
    start_date: date
    end_date: date
    notes: str | None = None
