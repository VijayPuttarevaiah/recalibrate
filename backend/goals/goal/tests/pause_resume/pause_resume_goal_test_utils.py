"""Shared helpers/constants for pause/resume goal unit tests."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock


HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_BAD_GATEWAY = 502

DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
ALT_GOAL_ID = 5

COMPLETED_COUNT = 5
TOTAL_TASK_COUNT = 10
PENDING_TASK_COUNT = 2

PAUSED_AT = datetime(2026, 3, 20, 10, 0, 0)

MOCK_STATS = {
    "completed": COMPLETED_COUNT,
    "missed": 0,
    "total_tasks": TOTAL_TASK_COUNT,
}
MOCK_TASKS = [{"title": "Task 1", "date": "2026-04-05"}]


def make_goal(status: str = "in_progress", paused_at=None, end_date=None):
    goal = MagicMock()
    goal.id = DEFAULT_GOAL_ID
    goal.user_id = DEFAULT_USER_ID
    goal.status = status
    goal.paused_at = paused_at
    goal.start_date = date(2026, 1, 1)
    goal.end_date = end_date or date(2026, 6, 30)
    goal.title = "Learn Python"
    goal.category = "learning"
    goal.notes = "Focus on advanced topics"
    return goal


def make_task(id: int = 1, status: str = "pending"):
    task = MagicMock()
    task.id = id
    task.goal_id = DEFAULT_GOAL_ID
    task.status = status
    task.due_date = date(2026, 4, 15)
    return task


def mock_db(goal=None, task_list=None):
    """Create a mock DB session with pre-configured query chains."""

    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = goal

    if task_list is not None:
        filtered.all.return_value = task_list

    filtered.order_by.return_value.all.return_value = task_list or []
    filtered.count.return_value = len(task_list) if task_list else 0

    return db


RESUME_PATCHES = [
    "goals.goal.service.generate_resume_tasks",
    "goals.goal.service.gather_research",
    "goals.goal.service.format_summary_for_llm",
    "goals.goal.service.build_progress_summary",
]


def apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen):
    mock_summary.return_value = {"stats": MOCK_STATS}
    if mock_research is not None:
        mock_research.return_value = "research"
    mock_gen.return_value = MOCK_TASKS
