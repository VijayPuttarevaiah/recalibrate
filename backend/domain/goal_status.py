"""Single source of truth for goal and task statuses."""

GOAL_STATUSES = {"pending", "in_progress", "completed", "paused"}
PAUSABLE_GOAL_STATUSES = {"pending", "in_progress"}
TASK_STATUSES = {"pending", "completed", "missed", "skipped"}
