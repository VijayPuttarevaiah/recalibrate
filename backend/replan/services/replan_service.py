"""Backward-compatible re-exports. Canonical code split into feature folders."""

from replan.detect.service import detect_missed_tasks
from replan.check.service import check_goal_needs_replan, DEFAULT_REPLAN_THRESHOLD
from replan.goal.service import (
    replan_goal,
    ReplanContext,
    _get_goal_or_404,
    _ensure_goal_not_ended,
    _generate_all_new_tasks,
    _mark_missed_tasks,
    _delete_future_pending_tasks,
    _insert_new_tasks,
    _generate_replan_tasks,
    _generate_explanation,
    _call_llm_for_tasks,
)
from goals.ai.llm_service import _strip_code_fences, extract_json, _validate_task_list
