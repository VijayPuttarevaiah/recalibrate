


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from datetime import date
from utils.db_session import DBSession
from services.goal_service import create_goal_with_tasks
def run():
    db = DBSession().SessionLocal()

    goal = create_goal_with_tasks(
        db=db,
        user_id=1,
        goal_text="Learn Python in 30 days",
        category="learning",
        start_date=date(2026, 2, 10),
        end_date=date(2026, 3, 10),
        constraints="1 hour per day"
    )

    print("Created goal:", goal.id)

if __name__ == "__main__":
    run()
