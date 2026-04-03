# services/goal_service.py
from datetime import date, datetime, timedelta
from goals.models.goal_models import Goal
from goals.models.task_models import Task
from goals.ai.llm_service import generate_tasks_llm, TaskGenerationContext
from goals.integrations.web_search_service import gather_research
from goals.progress.summarizer import build_progress_summary, format_summary_for_llm
from replan.goal.service import generate_resume_tasks
from fastapi import HTTPException, status

PAUSABLE_STATUSES = {"pending", "in_progress"}


def _goal_dict(goal: Goal, task_count: int | None = None) -> dict:
    payload = {
        "id": goal.id,
        "title": goal.title,
        "category": goal.category,
        "notes": goal.notes,
        "start_date": goal.start_date,
        "end_date": goal.end_date,
        "status": goal.status,
        "paused_at": goal.paused_at,
    }
    if task_count is not None:
        payload["task_count"] = task_count
    return payload


def get_user_goals(db, user_id: int):
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()

    result = []
    for goal in goals:
        task_count = db.query(Task).filter(Task.goal_id == goal.id).count()
        result.append(
            {
                **_goal_dict(goal, task_count=task_count),
            }
        )

    return result


def get_goal_tasks(db, user_id: int, goal_id: int):
    goal = (
        db.query(Goal)
        .filter(
            Goal.id == goal_id,
            Goal.user_id == user_id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or does not belong to this user",
        )

    tasks = db.query(Task).filter(Task.goal_id == goal_id).order_by(Task.due_date).all()

    return {
        **_goal_dict(goal, task_count=len(tasks)),
        "tasks": [
            {
                "id": t.id,
                "goal_id": t.goal_id,
                "title": t.title,
                "description": t.description,
                "due_date": t.due_date,
                "status": t.status,
                "notes": t.notes,
            }
            for t in tasks
        ],
    }


def create_goal_with_tasks(db, goal_data):
    category_value = (
        goal_data.category.value
        if hasattr(goal_data.category, "value")
        else goal_data.category
    )

    goal = Goal(
        user_id=goal_data.user_id,
        title=goal_data.goal,
        category=category_value,
        start_date=goal_data.start_date,
        end_date=goal_data.end_date,
        notes=goal_data.notes,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    # --- Do web research ONCE for the entire goal ---
    print(f"\n Researching: {goal_data.goal} [{goal_data.category}]")
    research_context = gather_research(
        goal_data.goal,
        goal_data.category,
        goal_data.notes,
    )
    print(f"\n Research gathered ({len(research_context)} chars)")

    # --- Batch LLM calls in 30-day chunks, reusing research ---
    current_start = goal_data.start_date

    while current_start <= goal_data.end_date:
        current_end = min(
            current_start + timedelta(days=29),
            goal_data.end_date,
        )

        task_context = TaskGenerationContext(
            goal=goal_data.goal,
            category=category_value,
            start_date=current_start,
            end_date=current_end,
            notes=goal_data.notes,
            research_context=research_context,  # pass research to every chunk
        )
        tasks = generate_tasks_llm(task_context)

        print(f"\n Generated {len(tasks)} tasks for {current_start} → {current_end}")

        for t in tasks:
            task = Task(
                goal_id=goal.id,
                title=t["title"],
                due_date=t["date"],
            )
            db.add(task)

        db.commit()
        current_start = current_end + timedelta(days=1)

    return goal


def _get_user_goal(db, user_id: int, goal_id: int) -> Goal:
    """Fetch a goal owned by the given user or raise 404."""
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == user_id,
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found or does not belong to this user",
        )
    return goal


def pause_goal(db, user_id: int, goal_id: int) -> dict:
    """Pause an active goal — sets status to 'paused' and records timestamp."""
    goal = _get_user_goal(db, user_id, goal_id)

    if goal.status not in PAUSABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause a goal with status '{goal.status}'. "
                   f"Only goals with status {PAUSABLE_STATUSES} can be paused.",
        )

    goal.status = "paused"
    goal.paused_at = datetime.utcnow()
    db.commit()

    return {
        "goal_id": goal.id,
        "status": "paused",
        "paused_at": goal.paused_at.isoformat(),
        "message": "Goal paused successfully. All reminders stopped.",
    }


def resume_goal(db, user_id: int, goal_id: int, body=None) -> dict:
    """Resume a paused goal with LLM-regenerated tasks.

    Two modes:
    - keep_original: compress remaining tasks into original end_date
    - new_end_date: regenerate tasks from today to the new deadline
    """
    goal = _get_user_goal(db, user_id, goal_id)

    if goal.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume a goal with status '{goal.status}'. "
                   f"Only paused goals can be resumed.",
        )

    today = date.today()

    if body and body.mode == "new_end_date":
        effective_end_date = body.new_end_date
    else:
        effective_end_date = goal.end_date

    if effective_end_date <= today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot resume: the target end date has already passed.",
        )

    summary = build_progress_summary(db, goal_id, as_of=today)
    progress_text = format_summary_for_llm(summary, goal.title)
    research_context = gather_research(goal.title, goal.category, goal.notes)

    all_new_tasks = []
    current_start = today
    while current_start <= effective_end_date:
        current_end = min(current_start + timedelta(days=29), effective_end_date)
        new_tasks = generate_resume_tasks(
            goal_title=goal.title,
            category=goal.category,
            start_date=current_start,
            end_date=current_end,
            goal_end_date=effective_end_date,
            notes=goal.notes,
            progress_context=progress_text,
            research_context=research_context,
        )
        all_new_tasks.extend(new_tasks)
        current_start = current_end + timedelta(days=1)

    if len(all_new_tasks) == 0:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resume failed: could not generate new tasks. "
                   "Your goal has NOT been modified. Please try again.",
        )

    pending_tasks = (
        db.query(Task)
        .filter(Task.goal_id == goal_id, Task.status == "pending")
        .all()
    )
    tasks_deleted = len(pending_tasks)
    for task in pending_tasks:
        db.delete(task)
    db.flush()

    for t in all_new_tasks:
        db.add(Task(goal_id=goal.id, title=t["title"], due_date=t["date"], status="pending"))
    db.flush()

    goal.end_date = effective_end_date
    goal.status = "in_progress"
    goal.paused_at = None
    db.commit()

    return {
        "adjusted": True,
        "goal_id": goal.id,
        "status": "in_progress",
        "stats": {
            "completed_tasks": summary["stats"]["completed"],
            "old_pending_removed": tasks_deleted,
            "new_tasks_generated": len(all_new_tasks),
            "remaining_days": (effective_end_date - today).days,
        },
        "new_end_date": effective_end_date.isoformat(),
        "message": f"Goal resumed with {len(all_new_tasks)} new tasks generated.",
    }
