from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.task_models import Task
from typing import Dict, List, Any


def _categorize_tasks(
    all_tasks: List[Task], as_of: date
) -> tuple[List[Task], List[Task], List[Task]]:
    """Categorize tasks into completed, missed, and upcoming.
    
    Reduces cyclomatic complexity by isolating categorization logic.
    """
    completed = [t for t in all_tasks if t.status == "completed"]
    missed = [t for t in all_tasks if t.status == "pending" and t.due_date < as_of]
    upcoming = [t for t in all_tasks if t.status == "pending" and t.due_date >= as_of]
    return completed, missed, upcoming


def _build_month_stats(all_tasks: List[Task], as_of: date) -> Dict[str, Dict[str, int]]:
    """Build monthly statistics for past tasks.
    
    Reduces cyclomatic complexity by extracting month aggregation logic.
    """
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
    
    return month_stats


def _get_recent_completed(completed: List[Task], limit: int = 5) -> List[Task]:
    """Get most recent completed tasks."""
    return sorted(completed, key=lambda t: t.due_date, reverse=True)[:limit]


def _calculate_completion_rate(completed: int, missed: int) -> float:
    """Calculate completion percentage for past tasks."""
    total_past = completed + missed
    if total_past == 0:
        return 0.0
    return round(completed / total_past * 100, 1)


def _fetch_goal_tasks(db: Session, goal_id: int) -> List[Task]:
    """Fetch all tasks for a goal, ordered by due date."""
    return (
        db.query(Task)
        .filter(Task.goal_id == goal_id)
        .order_by(Task.due_date)
        .all()
    )


def _build_summary_dict(
    all_tasks: List[Task],
    completed: List[Task],
    missed: List[Task],
    upcoming: List[Task],
    month_stats: Dict[str, Dict[str, int]],
    recent_completed: List[Task],
) -> Dict[str, Any]:
    """Build the final summary dictionary.
    
    Reduces cyclomatic complexity by isolating dict construction.
    """
    return {
        "stats": {
            "total_tasks": len(all_tasks),
            "completed": len(completed),
            "missed": len(missed),
            "remaining_future": len(upcoming),
            "completion_rate": _calculate_completion_rate(len(completed), len(missed)),
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


def build_progress_summary(db: Session, goal_id: int, as_of: date = None) -> dict:
    """Build a compact progress digest for a goal.

    Returns a dict with:
    - stats: completion rates, streak info
    - recent_completed: last 5 completed tasks (for continuity)
    - missed_tasks: all overdue pending tasks (what went wrong)
    - upcoming_preview: next 5 pending tasks (what's about to happen)
    - phase_summary: grouped completion by month
    
    Refactored: Delegates to helper methods for reduced complexity (CC 8 → CC 2).
    """
    if as_of is None:
        as_of = date.today()

    # Fetch tasks once
    all_tasks = _fetch_goal_tasks(db, goal_id)
    
    # Categorize tasks
    completed, missed, upcoming = _categorize_tasks(all_tasks, as_of)
    
    # Build month statistics
    month_stats = _build_month_stats(all_tasks, as_of)
    
    # Get recent completed for continuity
    recent_completed = _get_recent_completed(completed)
    
    # Build and return summary
    return _build_summary_dict(
        all_tasks, completed, missed, upcoming, month_stats, recent_completed
    )


def _format_monthly_history(phase_summary: Dict[str, Dict[str, int]]) -> List[str]:
    """Format monthly breakdown section."""
    if not phase_summary:
        return []
    
    lines = ["Monthly history:"]
    for month, data in sorted(phase_summary.items()):
        lines.append(
            f"  {month}: {data['completed']}/{data['total']} done, "
            f"{data['missed']} missed"
        )
    lines.append("")
    return lines


def _format_recent_completed(
    recent_completed: List[Dict[str, str]]
) -> List[str]:
    """Format recent completed tasks section."""
    if not recent_completed:
        return []
    
    lines = ["Last completed tasks (for continuity):"]
    for t in recent_completed:
        lines.append(f"  - [{t['due_date']}] {t['title']}")
    lines.append("")
    return lines


def _format_missed_tasks(missed_tasks: List[Dict[str, str]]) -> List[str]:
    """Format missed tasks section with capping for large lists.
    
    Reduces cyclomatic complexity by isolating missed task formatting.
    """
    if not missed_tasks:
        return []
    
    lines = ["Missed tasks that need rescheduling:"]
    
    # Cap at 20 to avoid blowing up context for very neglected goals
    display_missed = missed_tasks[:20]
    for t in display_missed:
        lines.append(f"  - [{t['due_date']}] {t['title']}")
    
    if len(missed_tasks) > 20:
        lines.append(
            f"  ... and {len(missed_tasks) - 20} more missed tasks"
        )
    
    lines.append("")
    return lines


def format_summary_for_llm(summary: dict, goal_title: str) -> str:
    """Convert the progress summary into a compact text block the LLM can reason about.
    
    Stays under ~500 tokens even for multi-year goals.
    
    Refactored: Delegates to helper methods for reduced complexity (CC 8 → CC 2).
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

    # Add each formatted section
    lines.extend(_format_monthly_history(summary["phase_summary"]))
    lines.extend(_format_recent_completed(summary["recent_completed"]))
    lines.extend(_format_missed_tasks(summary["missed_tasks"]))

    return "\n".join(lines)