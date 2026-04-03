"""
Core replanning engine.

Flow:
1. Detect missed tasks (pending + overdue)
2. Summarize progress (compact, LLM-friendly)
3. Delete all future pending tasks
4. Ask LLM to regenerate from today → end_date using progress context
5. Ask LLM for a trade-off explanation
6. Save new tasks + adjustment log
"""

import json
import re
import os
import requests
from datetime import date, timedelta
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from goals.models.goal_models import Goal
from goals.models.task_models import Task
from goals.models.goal_adjustment_models import GoalAdjustment
from goals.progress.summarizer import build_progress_summary, format_summary_for_llm
from goals.integrations.web_search_service import gather_research
from goals.ai.llm_service import _strip_code_fences, extract_json, _validate_task_list
from replan.detect.service import detect_missed_tasks


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"
MAX_MISSED_TITLES_FOR_PROMPT = 10
EXPLANATION_TEMPERATURE = 0.3
TASK_GENERATION_TEMPERATURE = 0.2
CHUNK_DAYS = 29  # ~30-day windows to keep prompts within token limits


def _get_goal_or_404(db: Session, user_id: int, goal_id: int) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or does not belong to this user",
        )
    return goal


def _ensure_goal_not_ended(goal: Goal, today: date) -> None:
    if goal.end_date <= today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal has already ended. Nothing to replan.",
        )


def _generate_all_new_tasks(
    goal: Goal,
    today: date,
    progress_text: str,
) -> list[dict]:
    research_context = gather_research(goal.title, goal.category, goal.notes)
    all_new_tasks: list[dict] = []
    current_start = today

    while current_start <= goal.end_date:
        current_end = min(
            current_start + timedelta(days=CHUNK_DAYS),
            goal.end_date,
        )

        context = ReplanContext(
            goal_title=goal.title,
            category=goal.category,
            start_date=current_start,
            end_date=current_end,
            goal_end_date=goal.end_date,
            notes=goal.notes,
            progress_context=progress_text,
            research_context=research_context,
        )
        new_tasks = _generate_replan_tasks(context)

        all_new_tasks.extend(new_tasks)
        current_start = current_end + timedelta(days=1)

    return all_new_tasks


def _mark_missed_tasks(db: Session, goal_id: int) -> list[Task]:
    missed_tasks = detect_missed_tasks(db, goal_id)
    for task in missed_tasks:
        task.status = "missed"
    db.flush()
    return missed_tasks


def _delete_future_pending_tasks(db: Session, goal_id: int, today: date) -> int:
    future_pending = (
        db.query(Task)
        .filter(
            Task.goal_id == goal_id,
            Task.status == "pending",
            Task.due_date >= today,
        )
        .all()
    )
    tasks_deleted = len(future_pending)
    for task in future_pending:
        db.delete(task)
    db.flush()
    return tasks_deleted


def _insert_new_tasks(db: Session, goal_id: int, tasks: list[dict]) -> None:
    for task in tasks:
        db.add(
            Task(
                goal_id=goal_id,
                title=task["title"],
                due_date=task["date"],
                status="pending",
            )
        )
    db.flush()


# ─── Replanning ──────────────────────────────────────────────────────


def replan_goal(db: Session, user_id: int, goal_id: int) -> dict:
    """
    Main entry point: detect problems, regenerate future tasks,
    explain trade-offs.
    """

    # 1. Validate ownership
    goal = _get_goal_or_404(db, user_id, goal_id)

    if goal.status == "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot replan a paused goal. Resume it first.",
        )

    today = date.today()

    _ensure_goal_not_ended(goal, today)

    # 2. Build progress summary (compact — works for 2-year goals)
    summary = build_progress_summary(db, goal_id, as_of=today)
    progress_text = format_summary_for_llm(summary, goal.title)

    missed_count = summary["stats"]["missed"]
    if missed_count == 0:
        return {
            "adjusted": False,
            "message": "No missed tasks detected. Plan is on track.",
            "stats": summary["stats"],
        }

    # ──────────────────────────────────────────────────────────────
    # 3. GENERATE NEW TASKS FIRST (before deleting anything!)
    #    If LLM fails, we abort and keep the old plan intact.
    # ──────────────────────────────────────────────────────────────
    all_new_tasks = _generate_all_new_tasks(
        goal=goal,
        today=today,
        progress_text=progress_text,
    )

    # ──────────────────────────────────────────────────────────────
    # 5. SAFETY CHECK: if LLM generated nothing, ABORT.
    #    Don't delete old tasks — keep the existing plan.
    # ──────────────────────────────────────────────────────────────
    if len(all_new_tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Replan failed: LLM could not generate replacement tasks. "
                "Your existing plan has NOT been modified. "
                "Please try again in a moment."
            ),
        )

    # ──────────────────────────────────────────────────────────────
    # 6. NOW safe to modify the database — we have replacement tasks
    # ──────────────────────────────────────────────────────────────

    # Mark overdue tasks as "missed"
    _mark_missed_tasks(db, goal_id)

    # Delete old future pending tasks
    tasks_deleted = _delete_future_pending_tasks(db, goal_id, today)

    # Insert the new tasks
    _insert_new_tasks(db, goal.id, all_new_tasks)

    # 7. Generate trade-off explanation
    explanation = _generate_explanation(
        goal_title=goal.title,
        category=goal.category,
        summary=summary,
        new_task_count=len(all_new_tasks),
        remaining_days=(goal.end_date - today).days,
    )

    # 8. Log the adjustment
    adjustment = GoalAdjustment(
        goal_id=goal.id,
        missed_task_count=missed_count,
        completed_task_count=summary["stats"]["completed"],
        total_task_count=summary["stats"]["total_tasks"],
        tasks_deleted=tasks_deleted,
        tasks_created=len(all_new_tasks),
        original_end_date=goal.end_date,
        new_end_date=goal.end_date,
        explanation=explanation,
    )
    db.add(adjustment)
    db.commit()

    return {
        "adjusted": True,
        "goal_id": goal.id,
        "stats": {
            "missed_tasks_found": missed_count,
            "old_future_tasks_removed": tasks_deleted,
            "new_tasks_generated": len(all_new_tasks),
            "remaining_days": (goal.end_date - today).days,
        },
        "explanation": explanation,
        "adjustment_id": adjustment.id,
    }


# ─── LLM Calls ──────────────────────────────────────────────────────


@dataclass
class ReplanContext:
    goal_title: str
    category: str
    start_date: date
    end_date: date
    goal_end_date: date
    notes: Optional[str]
    progress_context: str
    research_context: str


def _generate_replan_tasks(context: ReplanContext):
    """Generate adjusted tasks using progress context + research."""
    prompt_lines = [
        "You are replanning a goal because the user fell behind schedule.",
        "",
        f"Goal: {context.goal_title}",
        f"Category: {context.category}",
        f"This chunk: {context.start_date} → {context.end_date}",
        f"Goal final deadline: {context.goal_end_date}",
        f"Notes: {context.notes or 'None'}",
        "",
        context.progress_context,
        "",
        context.research_context,
        "",
        "=== REPLANNING INSTRUCTIONS ===",
        "",
        "The user has fallen behind. You must create a REALISTIC adjusted plan:",
        "",
        "1. PRIORITIZE critical tasks that were missed — reschedule the most",
        "   important ones first",
        "2. COMBINE or COMPRESS lower-priority tasks to save time",
        "3. INCREASE intensity slightly where feasible (e.g., 2 topics per day",
        "   instead of 1) but stay realistic",
        "4. DROP tasks that are nice-to-have but not essential if time is tight",
        "5. Maintain proper sequencing — don't schedule advanced tasks before",
        "   prerequisites",
        "",
        "Rules:",
        "- One task per day (every day from",
        f"  {context.start_date} to {context.end_date})",
        "- Tasks must account for the user's actual progress (see completed tasks)",
        "- Tasks must pick up where the user left off, not restart from scratch",
        "- Be specific and actionable",
        "- Return ONLY valid JSON array",
        "",
        "Format:",
        "[",
        '  {"title": "Specific actionable task", "date": "YYYY-MM-DD"}',
        "]",
    ]
    prompt = "\n".join(prompt_lines)

    return _call_llm_for_tasks(prompt)


def _generate_explanation(
    goal_title,
    category,
    summary,
    new_task_count,
    remaining_days,
):
    """Ask LLM to explain the trade-offs in plain language."""

    stats = summary["stats"]
    missed_titles = [
        task["title"] for task in summary["missed_tasks"][:MAX_MISSED_TITLES_FOR_PROMPT]
    ]

    prompt_lines = [
        "You adjusted a user's goal plan. Explain the changes clearly and briefly.",
        "",
        f"Goal: {goal_title}",
        f"Category: {category}",
        f"Progress: {stats['completed']} completed, {stats['missed']} missed",
        f"New plan: {new_task_count} tasks over {remaining_days} days remaining",
        "",
        "Missed tasks included:",
        json.dumps(missed_titles, indent=2),
        "",
        "Write a 3-5 sentence explanation that covers:",
        "1. What went wrong (how many tasks missed, which area)",
        "2. What changed in the new plan (combined tasks, increased pace,",
        "   dropped items)",
        "3. Key trade-offs the user should know about",
        "",
        "Keep it friendly and motivating, not judgmental.",
        "Be specific about what was adjusted — don't be vague.",
        "",
        "Return ONLY the explanation text, no JSON, no markdown headers.",
    ]
    prompt = "\n".join(prompt_lines)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a supportive productivity coach. Be concise and specific.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": EXPLANATION_TEMPERATURE,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Explanation generation error: {e}")
        return (
            f"Your plan was adjusted because {stats['missed']} tasks were overdue. "
            f"The remaining {new_task_count} tasks have been redistributed across "
            f"{remaining_days} days. Some tasks were combined to catch up."
        )




def _call_llm_for_tasks(prompt: str) -> list[dict]:
    """Shared LLM call logic for task generation."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a replanning assistant. Generate adjusted tasks "
                    "based on the user's actual progress. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": TASK_GENERATION_TEMPERATURE,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        content = _strip_code_fences(content)

        json_array = extract_json(content)
        if not json_array:
            raise ValueError("No JSON array found in response")
        tasks = json.loads(json_array)
        _validate_task_list(tasks)

        return tasks

    except Exception as e:
        print(f"Replan LLM error: {e}")
        return []


def generate_resume_tasks(context: ReplanContext):
    """Generate tasks for a resumed goal. Public API used by resume_goal."""

    prompt = f"""
You are creating a plan for a goal that was paused and is now being resumed.

Goal: {context.goal_title}
Category: {context.category}
This chunk: {context.start_date} → {context.end_date}
Goal final deadline: {context.goal_end_date}
Notes: {context.notes or "None"}

{context.progress_context}

{context.research_context}

=== RESUME INSTRUCTIONS ===

The user paused this goal and is resuming. Create a REALISTIC adjusted plan:

1. CONTINUE from where the user left off — use completed tasks as context
2. COMPRESS remaining work into the available time
3. PRIORITIZE the most important remaining items
4. COMBINE or MERGE related tasks if time is tight
5. DROP nice-to-have tasks if essential ones need more time
6. Maintain proper sequencing — prerequisites before advanced tasks

Rules:
- One task per day (every day from {context.start_date} to {context.end_date})
- Tasks must build on the user's completed progress (see completed tasks)
- Tasks must pick up where the user left off, not restart from scratch
- Be specific and actionable
- Return ONLY valid JSON array

Format:
[
  {{"title": "Specific actionable task", "date": "YYYY-MM-DD"}}
]
"""

    return _call_llm_for_tasks(prompt)
