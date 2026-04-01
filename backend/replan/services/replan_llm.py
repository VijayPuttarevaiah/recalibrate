"""Backward-compatible re-exports. Canonical code in replan/llm/service.py"""
from replan.llm.service import *  # noqa: F401,F403
from replan.llm.service import (
    ReplanTaskRequest,
    generate_replan_tasks,
    generate_replan_explanation,
    _strip_code_fences,
    _extract_json_array,
    _validate_task_structure,
    _validate_date_string,
    _call_llm_for_tasks,
)
