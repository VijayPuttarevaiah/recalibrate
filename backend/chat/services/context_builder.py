"""Context-building utilities for chat.

This module exists to keep `chat_service.py` focused on orchestration and I/O.
All functions here are pure (except the DB query in `build_goal_context`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from goals.models.goal_models import Goal
from goals.models.task_models import Task

# --- Extracted Constants ---
UPCOMING_TASKS_LIMIT = 7
RECENT_TASKS_LIMIT = 5
NOTES_SNIPPET_LENGTH = 100
OVERDUE_TASKS_LIMIT = 5


@dataclass(frozen=True)
class GoalStatsContext:
    goal: Goal
    tasks: list
    completed: list
    pending: list
    missed: list
    overdue: list
    today: date


def _format_goal_stats(context: GoalStatsContext) -> str:
    lines = [
        "=== GOAL CONTEXT ===",
        f"Title: {context.goal.title}",
        f"Category: {context.goal.category}",
        f"Timeline: {context.goal.start_date} → {context.goal.end_date}",
        f"Status: {context.goal.status}",
        f"Notes: {context.goal.notes or 'None'}",
        "",
        "=== PROGRESS ===",
        f"Total tasks: {len(context.tasks)}",
        f"Completed: {len(context.completed)}",
        f"Pending: {len(context.pending)}",
        f"Missed: {len(context.missed)}",
        f"Overdue: {len(context.overdue)}",
        f"Days remaining: {(context.goal.end_date - context.today).days}",
        "",
    ]
    return "\n".join(lines)


def _append_recent_completed(lines: list[str], completed: list) -> None:
    lines.append(f"=== RECENTLY COMPLETED (last {RECENT_TASKS_LIMIT}) ===")
    for task in completed[-RECENT_TASKS_LIMIT:]:
        notes_snippet = f" | Notes: {task.notes[:NOTES_SNIPPET_LENGTH]}" if task.notes else ""
        lines.append(f"- [{task.due_date}] {task.title}{notes_snippet}")


def _append_today_tasks(lines: list[str], today_tasks: list) -> None:
    lines.append("")
    lines.append("=== TODAY'S TASKS ===")
    if today_tasks:
        for task in today_tasks:
            lines.append(f"- {task.title} (status: {task.status})")
        return
    lines.append("- No tasks scheduled for today")


def _append_upcoming_tasks(lines: list[str], upcoming: list) -> None:
    lines.append("")
    lines.append("=== UPCOMING (next 7 days) ===")
    for task in upcoming:
        lines.append(f"- [{task.due_date}] {task.title}")


def _append_overdue_tasks(lines: list[str], overdue: list) -> None:
    if not overdue:
        return
    lines.append("")
    lines.append("=== OVERDUE TASKS ===")
    for task in overdue[:OVERDUE_TASKS_LIMIT]:
        lines.append(f"- [{task.due_date}] {task.title}")


def _format_task_lists(
    completed: list,
    today_tasks: list,
    upcoming: list,
    overdue: list,
) -> str:
    lines: list[str] = []
    _append_recent_completed(lines, completed)
    _append_today_tasks(lines, today_tasks)
    _append_upcoming_tasks(lines, upcoming)
    _append_overdue_tasks(lines, overdue)
    return "\n".join(lines) + "\n"


def build_goal_context(db: Session, goal: Goal) -> str:
    """Build a rich context string from goal + its tasks."""

    tasks = db.query(Task).filter(Task.goal_id == goal.id).order_by(Task.due_date).all()

    today = date.today()

    completed = [t for t in tasks if t.status == "completed"]
    pending = [t for t in tasks if t.status == "pending"]
    missed = [t for t in tasks if t.status == "missed"]
    overdue = [t for t in tasks if t.status == "pending" and t.due_date < today]

    today_tasks = [t for t in tasks if t.due_date == today]
    upcoming = [t for t in pending if t.due_date > today][:UPCOMING_TASKS_LIMIT]

    stats_context = GoalStatsContext(
        goal=goal,
        tasks=tasks,
        completed=completed,
        pending=pending,
        missed=missed,
        overdue=overdue,
        today=today,
    )
    context = _format_goal_stats(stats_context)
    context += _format_task_lists(completed, today_tasks, upcoming, overdue)

    return context


def build_task_context(task: Task) -> str:
    """Build focused context for a specific task."""

    lines = [
        "=== FOCUSED TASK ===",
        f"Title: {task.title}",
        f"Due Date: {task.due_date}",
        f"Status: {task.status}",
        f"Description: {task.description or 'No description'}",
        f"User Notes: {task.notes or 'No notes yet'}",
        "",
    ]
    return "\n".join(lines)


def build_system_prompt(has_task_focus: bool) -> str:
    """System prompt for the chat assistant."""

    base_lines = [
        "You are an AI productivity coach embedded in a goal-tracking app.",
        "Your job is to help users understand and execute their goals and tasks.",
        "",
        "Your capabilities:",
        "1. EXPLAIN what a goal or task means in practical terms",
        "2. BREAK DOWN complex tasks into clear, actionable steps",
        "3. PROVIDE examples, best practices, and tips relevant to the task",
        "4. ANSWER follow-up questions conversationally",
        "5. MOTIVATE the user based on their actual progress",
        "",
        "Rules:",
        "- Be concise but thorough. Prefer short paragraphs over long walls of text.",
        "- Be specific to the user's actual goal and tasks — don't give generic advice.",
        "- Reference their progress data (completed tasks, missed tasks) when relevant.",
        "- If a task seems unclear, explain what it likely means AND suggest how to approach it.",
        "- If the user is behind schedule, be encouraging but honest about what needs to happen.",
        "- Use the task notes (if any) to understand what the user has already tried.",
        "- Format steps as numbered lists when breaking things down.",
        "- Keep responses under 400 words unless the user asks for more detail.",
    ]

    if has_task_focus:
        base_lines.extend(
            [
                "",
                "You are currently focused on a SPECIFIC TASK. Prioritize explaining that task,",
                "but you can reference the broader goal context when helpful.",
            ]
        )

    return "\n".join(base_lines) + "\n"
