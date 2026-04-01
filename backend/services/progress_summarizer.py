from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.task_models import Task

RECENT_TASKS_LIMIT = 5
MISSED_TASKS_DISPLAY_LIMIT = 20


def _summarize_month_stats(all_tasks: list[Task], as_of: date) -> dict:
    month_stats: dict[str, dict[str, int]] = {}
    for task in all_tasks:
        if task.due_date >= as_of:
            continue
        key = task.due_date.strftime("%Y-%m")
        if key not in month_stats:
            month_stats[key] = {"total": 0, "completed": 0, "missed": 0}
        month_stats[key]["total"] += 1
        if task.status == "completed":
            month_stats[key]["completed"] += 1
        else:
            month_stats[key]["missed"] += 1
    return month_stats


def _build_task_items(tasks: list[Task]) -> list[dict[str, str]]:
    return [
        {"title": task.title, "due_date": str(task.due_date)}
        for task in tasks
    ]


def _completion_rate(completed: int, missed: int) -> float:
    total = completed + missed
    if total == 0:
        return 0.0
    return round(completed / total * 100, 1)

def build_progress_summary(db: Session, goal_id: int, as_of: date = None) -> dict:
    """
    Build a compact progress digest for a goal.

    Returns a dict with:
    - stats: completion rates, streak info
    - recent_completed: last 5 completed tasks (for continuity)
    - missed_tasks: all overdue pending tasks (what went wrong)
    - upcoming_preview: next 5 pending tasks (what's about to happen)
    - phase_summary: grouped completion by month
    """
    if as_of is None:
        as_of = date.today()

    all_tasks = (
        db.query(Task)
        .filter(Task.goal_id == goal_id)
        .order_by(Task.due_date)
        .all()
    )

    # Categorize tasks
    completed = [t for t in all_tasks if t.status == "completed"]
    missed = [t for t in all_tasks if t.status == "pending" and t.due_date < as_of]
    upcoming = [t for t in all_tasks if t.status == "pending" and t.due_date >= as_of]

    # --- Phase summary: group by month for compact history ---
    month_stats = _summarize_month_stats(all_tasks, as_of)

    # --- Recent completed (for continuity context) ---
    recent_completed = sorted(
        completed,
        key=lambda t: t.due_date,
        reverse=True,
    )[:RECENT_TASKS_LIMIT]

    # --- Build the summary ---
    return {
        "stats": {
            "total_tasks": len(all_tasks),
            "completed": len(completed),
            "missed": len(missed),
            "remaining_future": len(upcoming),
            "completion_rate": _completion_rate(len(completed), len(missed)),
        },
        "missed_tasks": _build_task_items(missed),
        "recent_completed": _build_task_items(recent_completed),
        "upcoming_preview": _build_task_items(upcoming[:RECENT_TASKS_LIMIT]),
        "phase_summary": month_stats,
    }


def _append_monthly_history(lines: list[str], summary: dict) -> None:
    if not summary["phase_summary"]:
        return
    lines.append("Monthly history:")
    for month, data in sorted(summary["phase_summary"].items()):
        lines.append(
            f"  {month}: {data['completed']}/{data['total']} done, "
            f"{data['missed']} missed"
        )
    lines.append("")


def _append_recent_completed(lines: list[str], summary: dict) -> None:
    if not summary["recent_completed"]:
        return
    lines.append("Last completed tasks (for continuity):")
    for task in summary["recent_completed"]:
        lines.append(f"  - [{task['due_date']}] {task['title']}")
    lines.append("")


def _append_missed_tasks(lines: list[str], summary: dict) -> None:
    if not summary["missed_tasks"]:
        return
    lines.append("Missed tasks that need rescheduling:")
    display_missed = summary["missed_tasks"][:MISSED_TASKS_DISPLAY_LIMIT]
    for task in display_missed:
        lines.append(f"  - [{task['due_date']}] {task['title']}")
    remaining = len(summary["missed_tasks"]) - MISSED_TASKS_DISPLAY_LIMIT
    if remaining > 0:
        lines.append(f"  ... and {remaining} more missed tasks")
    lines.append("")


def format_summary_for_llm(summary: dict, goal_title: str) -> str:
    """
    Convert the progress summary into a compact text block
    the LLM can reason about. Stays under ~500 tokens even
    for multi-year goals.
    """
    stats = summary["stats"]

    lines = [
        "=== PROGRESS CONTEXT ===",
        f"Goal: {goal_title}",
        f"Overall: {stats['completed']}/{stats['total_tasks']} tasks done "
        f"({stats['completion_rate']}% of past tasks completed)",
        f"Missed/overdue: {stats['missed']} tasks",
        f"Remaining to plan: from today onwards",
        "",
    ]

    _append_monthly_history(lines, summary)
    _append_recent_completed(lines, summary)
    _append_missed_tasks(lines, summary)

    return "\n".join(lines)