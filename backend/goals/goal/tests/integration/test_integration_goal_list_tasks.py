"""Integration tests for goal list + goal tasks endpoints.

Split from the older monolithic `test_integration_goal_endpoints.py` to improve
DPy modularization metrics.
"""

from datetime import date, datetime, timedelta

from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from auth.models.user_models import User
from goals.models.goal_models import Goal
from goals.models.task_models import Task

DEFAULT_SEED_TASK_COUNT = 5
LIST_ENDPOINT_TASK_COUNT = 3
TASKS_ENDPOINT_TASK_COUNT = 2


def _seed_user(db):
    user = User(
        id=1,
        first_name="Test",
        last_name="User",
        email="test@example.com",
        password="x",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    return user


def _seed_goal(db, status="in_progress", end_date=None, paused_at=None):
    goal = Goal(
        user_id=1,
        title="Learn Python",
        category="learning",
        start_date=date(2026, 1, 1),
        end_date=end_date or date(2026, 12, 31),
        status=status,
        paused_at=paused_at,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _seed_tasks(db, goal_id, count=DEFAULT_SEED_TASK_COUNT, status="pending"):
    tasks = []
    for i in range(count):
        task = Task(
            goal_id=goal_id,
            title=f"Task {i + 1}",
            due_date=date.today() + timedelta(days=i + 1),
            status=status,
        )
        db.add(task)
        tasks.append(task)
    db.commit()
    return tasks


# GET /goals/


def test_goals_list_returns_empty_list(auth_client, db_session):
    _seed_user(db_session)

    resp = auth_client.get("/goals/")

    assert resp.status_code == HTTP_200_OK
    assert resp.json() == []


def test_goals_list_includes_task_count(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    _seed_tasks(db_session, goal.id, count=LIST_ENDPOINT_TASK_COUNT)

    resp = auth_client.get("/goals/")

    assert resp.status_code == HTTP_200_OK
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Learn Python"
    assert data[0]["task_count"] == LIST_ENDPOINT_TASK_COUNT
    assert data[0]["status"] == "in_progress"


def test_goals_list_returns_paused_at_field(auth_client, db_session):
    _seed_user(db_session)
    now = datetime(2026, 3, 20, 10, 0, 0)
    _seed_goal(db_session, status="paused", paused_at=now)

    resp = auth_client.get("/goals/")

    data = resp.json()
    assert data[0]["status"] == "paused"
    assert data[0]["paused_at"] is not None


# GET /goals/{id}/tasks


def test_goal_tasks_returns_goal_with_tasks(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    _seed_tasks(db_session, goal.id, count=TASKS_ENDPOINT_TASK_COUNT)

    resp = auth_client.get(f"/goals/{goal.id}/tasks")

    assert resp.status_code == HTTP_200_OK
    data = resp.json()
    assert data["title"] == "Learn Python"
    assert len(data["tasks"]) == TASKS_ENDPOINT_TASK_COUNT


def test_goal_tasks_404_missing_goal(auth_client, db_session):
    _seed_user(db_session)

    resp = auth_client.get("/goals/999/tasks")

    assert resp.status_code == HTTP_404_NOT_FOUND
