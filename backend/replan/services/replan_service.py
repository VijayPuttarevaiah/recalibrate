"""Backward-compatible re-exports. Canonical code split into feature folders."""

from replan.detect.service import detect_missed_tasks
from replan.check.service import check_goal_needs_replan

__all__ = ["detect_missed_tasks", "check_goal_needs_replan"]
