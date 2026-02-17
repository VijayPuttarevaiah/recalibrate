# services/goal_service.py
from datetime import timedelta
from models.goal_models import Goal
from models.task_models import Task
from services.llm_service import generate_tasks_llm
from services.web_search_service import gather_research


def create_goal_with_tasks(db, goal_data):
    goal = Goal(
        user_id=goal_data.user_id,
        title=goal_data.goal,
        category=goal_data.category,
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
        goal_data.goal, goal_data.category, goal_data.notes
    )
    print(f"\n Research gathered ({len(research_context)} chars)")

    # --- Batch LLM calls in 30-day chunks, reusing research ---
    current_start = goal_data.start_date

    while current_start <= goal_data.end_date:
        current_end = min(
            current_start + timedelta(days=29),
            goal_data.end_date,
        )

        tasks = generate_tasks_llm(
            goal_data.goal,
            goal_data.category,
            current_start,
            current_end,
            goal_data.notes,
            research_context=research_context,  # pass research to every chunk
        )

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