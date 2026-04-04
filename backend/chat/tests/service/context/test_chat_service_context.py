"""Context + prompt + rate-limit unit tests for `chat.services.chat_service`."""

from datetime import date, timedelta
from unittest.mock import MagicMock

from chat.services.chat_service import (
    build_goal_context,
    build_system_prompt,
    build_task_context,
    check_rate_limit,
)

from chat.tests.service.utils.chat_service_test_utils import (
    RATE_LIMIT_AT,
    RATE_LIMIT_BELOW,
    RATE_LIMIT_OVER,
    make_goal,
    make_task,
    set_rate_limit_count,
    set_task_query_results,
)


# Context Building


def test_includes_goal_title():
    db = MagicMock()
    goal = make_goal(title="Get into Dalhousie MACS")
    set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "Dalhousie" in ctx


def test_includes_category():
    db = MagicMock()
    goal = make_goal(category="career_and_learning")
    set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "career_and_learning" in ctx


def test_includes_progress_section():
    db = MagicMock()
    goal = make_goal()
    completed_task = make_task(status="completed")
    pending_task = make_task(status="pending")
    set_task_query_results(db, [completed_task, pending_task])

    ctx = build_goal_context(db, goal)
    assert "PROGRESS" in ctx
    assert "Completed: 1" in ctx
    assert "Pending: 1" in ctx


def test_includes_days_remaining():
    db = MagicMock()
    goal = make_goal(end_date=date.today() + timedelta(days=30))
    set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "Days remaining:" in ctx


def test_includes_today_section():
    db = MagicMock()
    goal = make_goal()
    set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "TODAY'S TASKS" in ctx


def test_includes_upcoming_section():
    db = MagicMock()
    goal = make_goal()
    set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "UPCOMING" in ctx


def test_task_includes_title():
    task = make_task(title="Write SOP")
    ctx = build_task_context(task)
    assert "Write SOP" in ctx


def test_task_includes_status():
    task = make_task(status="pending")
    ctx = build_task_context(task)
    assert "pending" in ctx


def test_task_includes_due_date():
    task = make_task(due_date=date(2026, 4, 15))
    ctx = build_task_context(task)
    assert "2026-04-15" in ctx


def test_task_desc_fallback():
    task = make_task(description=None)
    ctx = build_task_context(task)
    assert "No description" in ctx


def test_task_no_notes_fallback():
    task = make_task(notes=None)
    ctx = build_task_context(task)
    assert "No notes yet" in ctx


def test_task_notes_present():
    task = make_task(notes="Draft completed yesterday")
    ctx = build_task_context(task)
    assert "Draft completed yesterday" in ctx


# System prompt


def test_prompt_goal_no_task():
    prompt = build_system_prompt(has_task_focus=False)
    assert "productivity coach" in prompt
    assert "SPECIFIC TASK" not in prompt


def test_prompt_task_has_focus():
    prompt = build_system_prompt(has_task_focus=True)
    assert "SPECIFIC TASK" in prompt


def test_prompt_word_limit():
    prompt = build_system_prompt(has_task_focus=False)
    assert "400 words" in prompt


# Rate Limiting


def test_rate_allows_under():
    db = MagicMock()
    set_rate_limit_count(db, RATE_LIMIT_BELOW)
    assert check_rate_limit(db, user_id=1) is True


def test_rate_blocks_when_at_limit():
    db = MagicMock()
    set_rate_limit_count(db, RATE_LIMIT_AT)
    assert check_rate_limit(db, user_id=1) is False


def test_rate_blocks_over():
    db = MagicMock()
    set_rate_limit_count(db, RATE_LIMIT_OVER)
    assert check_rate_limit(db, user_id=1) is False
