# services/replan_service.py
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
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.goal_models import Goal
from models.task_models import Task
from models.goal_adjustment_models import GoalAdjustment
from services.progress_summarizer import build_progress_summary, format_summary_for_llm
from services.web_search_service import gather_research


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"


# ─── Detection ────────────────────────────────────────────────────────

def detect_missed_tasks(db: Session, goal_id: int) -> list[Task]:
    """Find all pending tasks whose due_date has passed."""
    today = date.today()
    return (
        db.query(Task)
        .filter(
            Task.goal_id == goal_id,
            Task.status == "pending",
            Task.due_date < today,
        )
        .order_by(Task.due_date)
        .all()
    )


def check_goal_needs_replan(db: Session, goal_id: int, threshold: int = 3) -> dict:
    """
    Quick check: does this goal need replanning?
    Returns status info without triggering a replan.
    
    threshold: minimum missed tasks before suggesting a replan (default 3)
    """
    missed = detect_missed_tasks(db, goal_id)
    total_past = (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.due_date < date.today())
        .count()
    )
    completed = (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.status == "completed")
        .count()
    )

    needs_replan = len(missed) >= threshold

    return {
        "goal_id": goal_id,
        "missed_count": len(missed),
        "completed_count": completed,
        "total_past_tasks": total_past,
        "threshold": threshold,
        "needs_replan": needs_replan,
    }


# ─── Replanning ──────────────────────────────────────────────────────

def replan_goal(db: Session, user_id: int, goal_id: int) -> dict:
    """
    Main entry point: detect problems, regenerate future tasks,
    explain trade-offs.
    """

    # 1. Validate ownership
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == user_id,
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or does not belong to this user",
        )

    today = date.today()

    if goal.end_date <= today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal has already ended. Nothing to replan.",
        )

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

    # 3. Gather fresh web research for context
    research_context = gather_research(goal.title, goal.category, goal.notes)

    # ──────────────────────────────────────────────────────────────
    # 4. GENERATE NEW TASKS FIRST (before deleting anything!)
    #    If LLM fails, we abort and keep the old plan intact.
    # ──────────────────────────────────────────────────────────────
    all_new_tasks = []
    current_start = today

    while current_start <= goal.end_date:
        current_end = min(
            current_start + timedelta(days=29),
            goal.end_date,
        )

        new_tasks = _generate_replan_tasks(
            goal_title=goal.title,
            category=goal.category,
            start_date=current_start,
            end_date=current_end,
            goal_end_date=goal.end_date,
            notes=goal.notes,
            progress_context=progress_text,
            research_context=research_context,
        )

        all_new_tasks.extend(new_tasks)
        current_start = current_end + timedelta(days=1)

    # ──────────────────────────────────────────────────────────────
    # 5. SAFETY CHECK: if LLM generated nothing, ABORT.
    #    Don't delete old tasks — keep the existing plan.
    # ──────────────────────────────────────────────────────────────
    if len(all_new_tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Replan failed: LLM could not generate replacement tasks. "
                f"Your existing plan has NOT been modified. "
                f"Please try again in a moment."
            ),
        )

    # ──────────────────────────────────────────────────────────────
    # 6. NOW safe to modify the database — we have replacement tasks
    # ──────────────────────────────────────────────────────────────

    # Mark overdue tasks as "missed"
    missed_tasks = detect_missed_tasks(db, goal_id)
    for task in missed_tasks:
        task.status = "missed"
    db.flush()

    # Delete old future pending tasks
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

    # Insert the new tasks
    for t in all_new_tasks:
        task = Task(
            goal_id=goal.id,
            title=t["title"],
            due_date=t["date"],
            status="pending",
        )
        db.add(task)
    db.flush()

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

def _generate_replan_tasks(
    goal_title, category, start_date, end_date, goal_end_date,
    notes, progress_context, research_context,
):
    """Generate adjusted tasks using progress context + research."""

    prompt = f"""
You are replanning a goal because the user fell behind schedule.

Goal: {goal_title}
Category: {category}
This chunk: {start_date} → {end_date}
Goal final deadline: {goal_end_date}
Notes: {notes or "None"}

{progress_context}

{research_context}

=== REPLANNING INSTRUCTIONS ===

The user has fallen behind. You must create a REALISTIC adjusted plan:

1. PRIORITIZE critical tasks that were missed — reschedule the most 
   important ones first
2. COMBINE or COMPRESS lower-priority tasks to save time
3. INCREASE intensity slightly where feasible (e.g., 2 topics per day 
   instead of 1) but stay realistic
4. DROP tasks that are nice-to-have but not essential if time is tight
5. Maintain proper sequencing — don't schedule advanced tasks before 
   prerequisites

Rules:
- One task per day (every day from {start_date} to {end_date})
- Tasks must account for the user's actual progress (see completed tasks)
- Tasks must pick up where the user left off, not restart from scratch
- Be specific and actionable
- Return ONLY valid JSON array

Format:
[
  {{"title": "Specific actionable task", "date": "YYYY-MM-DD"}}
]
"""

    return _call_llm_for_tasks(prompt)


def _generate_explanation(
    goal_title, category, summary, new_task_count, remaining_days,
):
    """Ask LLM to explain the trade-offs in plain language."""

    stats = summary["stats"]
    missed_titles = [t["title"] for t in summary["missed_tasks"][:10]]

    prompt = f"""
You adjusted a user's goal plan. Explain the changes clearly and briefly.

Goal: {goal_title}
Category: {category}
Progress: {stats['completed']} completed, {stats['missed']} missed
New plan: {new_task_count} tasks over {remaining_days} days remaining

Missed tasks included:
{json.dumps(missed_titles, indent=2)}

Write a 3-5 sentence explanation that covers:
1. What went wrong (how many tasks missed, which area)
2. What changed in the new plan (combined tasks, increased pace, dropped items)
3. Key trade-offs the user should know about

Keep it friendly and motivating, not judgmental. Be specific about 
what was adjusted — don't be vague.

Return ONLY the explanation text, no JSON, no markdown headers.
"""

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
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30,
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
                    "based on the user's actual progress. Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\[.*\]", content, re.DOTALL)
        if not match:
            raise ValueError("No JSON array found in LLM response")

        tasks = json.loads(match.group(0))
        if not isinstance(tasks, list):
            raise ValueError("LLM did not return a list")

        for t in tasks:
            if "title" not in t or "date" not in t:
                raise ValueError("Invalid task structure")

        return tasks

    except Exception as e:
        print(f"Replan LLM error: {e}")
        return []