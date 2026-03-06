"""
CYCLE 7 — build_progress_summary + format_summary_for_llm
RED   → required keys, completion rate never divides by zero
GREEN → counts correct, phase_summary groups by month, LLM text includes titles
REFACTOR → capped at 20 missed tasks, output under token budget
"""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
import re


def make_task(id, goal_id, title, status, due_date):
    t = MagicMock()
    t.id = id; t.goal_id = goal_id; t.title = title
    t.status = status; t.due_date = due_date
    return t


def make_db(tasks):
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = tasks
    return db


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_summary_has_required_top_level_keys():
    """RED: Summary must have: stats, missed_tasks, recent_completed, upcoming_preview, phase_summary."""
    from services.progress_summarizer import build_progress_summary
    result = build_progress_summary(make_db([]), goal_id=1, as_of=date.today())
    assert {"stats", "missed_tasks", "recent_completed", "upcoming_preview", "phase_summary"}.issubset(result.keys())


def test_RED_stats_has_all_required_fields():
    """RED: stats must include total_tasks, completed, missed, remaining_future, completion_rate."""
    from services.progress_summarizer import build_progress_summary
    result = build_progress_summary(make_db([]), goal_id=1, as_of=date.today())
    assert {"total_tasks", "completed", "missed", "remaining_future", "completion_rate"}.issubset(result["stats"].keys())


def test_RED_completion_rate_zero_for_empty_goal():
    """RED: 0 tasks must not cause ZeroDivisionError — return 0.0."""
    from services.progress_summarizer import build_progress_summary
    result = build_progress_summary(make_db([]), goal_id=1, as_of=date.today())
    assert result["stats"]["completion_rate"] == 0.0


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_counts_completed_tasks():
    """GREEN: All tasks with status='completed' are counted."""
    from services.progress_summarizer import build_progress_summary
    today = date.today()
    tasks = [
        make_task(1, 1, "Done 1", "completed", today - timedelta(days=3)),
        make_task(2, 1, "Done 2", "completed", today - timedelta(days=2)),
        make_task(3, 1, "Pending", "pending",  today + timedelta(days=1)),
    ]
    result = build_progress_summary(make_db(tasks), goal_id=1, as_of=today)
    assert result["stats"]["completed"] == 2


def test_GREEN_counts_missed_tasks():
    """GREEN: Pending tasks past due_date are counted as missed."""
    from services.progress_summarizer import build_progress_summary
    today = date.today()
    tasks = [
        make_task(1, 1, "Overdue 1", "pending", today - timedelta(days=2)),
        make_task(2, 1, "Overdue 2", "pending", today - timedelta(days=1)),
        make_task(3, 1, "Future",    "pending", today + timedelta(days=5)),
    ]
    result = build_progress_summary(make_db(tasks), goal_id=1, as_of=today)
    assert result["stats"]["missed"] == 2


def test_GREEN_completion_rate_correct_for_mixed():
    """GREEN: 2 completed + 2 missed = 50.0% completion rate."""
    from services.progress_summarizer import build_progress_summary
    today = date.today()
    tasks = [
        make_task(1, 1, "Done 1",  "completed", today - timedelta(days=4)),
        make_task(2, 1, "Done 2",  "completed", today - timedelta(days=3)),
        make_task(3, 1, "Missed 1","pending",   today - timedelta(days=2)),
        make_task(4, 1, "Missed 2","pending",   today - timedelta(days=1)),
    ]
    result = build_progress_summary(make_db(tasks), goal_id=1, as_of=today)
    assert result["stats"]["completion_rate"] == 50.0


def test_GREEN_phase_summary_keys_are_yyyy_mm():
    """GREEN: Phase summary keys must match YYYY-MM format."""
    from services.progress_summarizer import build_progress_summary
    today = date.today()
    tasks = [make_task(1, 1, "Old", "completed", today - timedelta(days=40))]
    result = build_progress_summary(make_db(tasks), goal_id=1, as_of=today)
    for key in result["phase_summary"].keys():
        assert re.match(r"^\d{4}-\d{2}$", key)


def test_GREEN_llm_format_includes_missed_task_titles():
    """GREEN: Missed task titles must appear in the LLM-formatted output."""
    from services.progress_summarizer import format_summary_for_llm
    summary = {
        "stats": {"completed": 0, "missed": 1, "total_tasks": 1, "completion_rate": 0.0},
        "missed_tasks": [{"title": "Study Chapter 5", "due_date": "2026-02-01"}],
        "recent_completed": [], "phase_summary": {},
    }
    result = format_summary_for_llm(summary, "Study for Exam")
    assert "Study Chapter 5" in result


def test_GREEN_llm_format_includes_progress_context_header():
    """GREEN: LLM output must include === PROGRESS CONTEXT === header."""
    from services.progress_summarizer import format_summary_for_llm
    summary = {
        "stats": {"completed": 0, "missed": 0, "total_tasks": 0, "completion_rate": 0.0},
        "missed_tasks": [], "recent_completed": [], "phase_summary": {},
    }
    assert "PROGRESS CONTEXT" in format_summary_for_llm(summary, "My Goal")


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_missed_tasks_capped_at_20():
    """REFACTOR: Even with 50 missed tasks, output shows max 20 + overflow note."""
    from services.progress_summarizer import format_summary_for_llm
    missed = [{"title": f"Missed Task {i}", "due_date": "2026-01-01"} for i in range(50)]
    summary = {
        "stats": {"completed": 0, "missed": 50, "total_tasks": 50, "completion_rate": 0.0},
        "missed_tasks": missed, "recent_completed": [], "phase_summary": {},
    }
    result = format_summary_for_llm(summary, "Big Goal")
    shown = sum(1 for i in range(50) if f"Missed Task {i}" in result)
    assert shown <= 20
    assert "more missed" in result.lower()


def test_REFACTOR_output_under_token_budget():
    """REFACTOR: Formatted output stays under ~3000 chars (≈500 tokens)."""
    from services.progress_summarizer import format_summary_for_llm
    missed = [{"title": f"Task {i}", "due_date": "2026-01-01"} for i in range(100)]
    summary = {
        "stats": {"completed": 5, "missed": 100, "total_tasks": 105, "completion_rate": 5.0},
        "missed_tasks": missed,
        "recent_completed": [{"title": "Last done", "due_date": "2026-02-01"}],
        "phase_summary": {},
    }
    assert len(format_summary_for_llm(summary, "Long Goal")) < 3000