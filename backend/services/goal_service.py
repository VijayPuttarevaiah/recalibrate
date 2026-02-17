from datetime import timedelta
from models.goal_models import Goal
from models.task_models import Task
from services.llm_service import generate_tasks_llm


def create_goal_with_tasks(db, goal_data):
    category_value = goal_data.category.value if hasattr(goal_data.category, "value") else goal_data.category

    goal = Goal(
        user_id=goal_data.user_id,
        title=goal_data.goal,
        category=category_value,
        start_date=goal_data.start_date,
        end_date=goal_data.end_date 
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    # Batch LLM calls in 30-day chunks
    current_start = goal_data.start_date

    while current_start <= goal_data.end_date:

        current_end = min(
            current_start + timedelta(days=29),
            goal_data.end_date
        )

        tasks = generate_tasks_llm(
            goal_data.goal,
            category_value,
            current_start,
            current_end,
            goal_data.notes
        )
        print("\nLLM RESPONSE:\n")
        print(tasks)
        for t in tasks:
            task = Task(
                goal_id=goal.id,
                title=t["title"],
                due_date=t["date"]
            )
            db.add(task)

        db.commit()

        current_start = current_end + timedelta(days=1)

    return goal
