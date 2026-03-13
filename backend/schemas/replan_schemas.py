# schemas/replan_schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional


class ReplanCheckResponse(BaseModel):
    goal_id: int
    missed_count: int
    completed_count: int
    total_past_tasks: int
    threshold: int
    needs_replan: bool


class ReplanStatsDetail(BaseModel):
    missed_tasks_found: int
    old_future_tasks_removed: int
    new_tasks_generated: int
    remaining_days: int


class ReplanResponse(BaseModel):
    adjusted: bool
    goal_id: Optional[int] = None
    message: Optional[str] = None
    stats: Optional[dict] = None
    explanation: Optional[str] = None
    adjustment_id: Optional[int] = None


class AdjustmentHistoryItem(BaseModel):
    id: int
    missed_task_count: int
    completed_task_count: int
    tasks_deleted: int
    tasks_created: int
    explanation: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)