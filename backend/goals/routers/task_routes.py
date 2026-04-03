"""Backward-compatible re-exports. Canonical code in goals/task/router.py"""

from goals.task.router import *  # noqa: F401,F403
from goals.task.router import (
    router,
    VALID_STATUSES,
    TaskStatusUpdate,
    TaskBatchUpdate,
    TaskNotesUpdate,
    _get_user_task,
    update_task_status,
    update_task_notes,
    get_task_detail,
    batch_update_tasks,
)
