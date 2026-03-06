from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.task_models import Task


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
    month_stats = {}
    for t in all_tasks:
        if t.due_date >= as_of:
            continue  # only summarize the past
        key = t.due_date.strftime("%Y-%m")
        if key not in month_stats:
            month_stats[key] = {"total": 0, "completed": 0, "missed": 0}
        month_stats[key]["total"] += 1
        if t.status == "completed":
            month_stats[key]["completed"] += 1
        else:
            month_stats[key]["missed"] += 1

    # --- Recent completed (last 5) for continuity context ---
    recent_completed = sorted(completed, key=lambda t: t.due_date, reverse=True)[:5]

    # --- Build the summary ---
    return {
        "stats": {
            "total_tasks": len(all_tasks),
            "completed": len(completed),
            "missed": len(missed),
            "remaining_future": len(upcoming),
            "completion_rate": (
                round(len(completed) / (len(completed) + len(missed)) * 100, 1)
                if (len(completed) + len(missed)) > 0
                else 0.0
            ),
        },
        "missed_tasks": [
            {"title": t.title, "due_date": str(t.due_date)}
            for t in missed
        ],
        "recent_completed": [
            {"title": t.title, "due_date": str(t.due_date)}
            for t in recent_completed
        ],
        "upcoming_preview": [
            {"title": t.title, "due_date": str(t.due_date)}
            for t in upcoming[:5]
        ],
        "phase_summary": month_stats,
    }


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

    # Monthly breakdown (very compact)
    if summary["phase_summary"]:
        lines.append("Monthly history:")
        for month, data in sorted(summary["phase_summary"].items()):
            lines.append(
                f"  {month}: {data['completed']}/{data['total']} done, "
                f"{data['missed']} missed"
            )
        lines.append("")

    # Recent completed (for continuity)
    if summary["recent_completed"]:
        lines.append("Last completed tasks (for continuity):")
        for t in summary["recent_completed"]:
            lines.append(f"  - [{t['due_date']}] {t['title']}")
        lines.append("")

    # Missed tasks (so LLM knows what to reschedule)
    if summary["missed_tasks"]:
        lines.append("Missed tasks that need rescheduling:")
        # Cap at 20 to avoid blowing up context for very neglected goals
        display_missed = summary["missed_tasks"][:20]
        for t in display_missed:
            lines.append(f"  - [{t['due_date']}] {t['title']}")
        if len(summary["missed_tasks"]) > 20:
            lines.append(
                f"  ... and {len(summary['missed_tasks']) - 20} more missed tasks"
            )
        lines.append("")

    return "\n".join(lines)