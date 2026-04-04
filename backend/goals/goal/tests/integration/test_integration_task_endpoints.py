"""Integration tests for task endpoints + replan check.

Split from the older monolithic `test_integration_goal_endpoints.py` to improve
DPy modularization metrics.
"""

from datetime import date, datetime, timedelta

from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from auth.models.user_models import User
from goals.models.goal_models import Goal
from goals.models.task_models import Task

DEFAULT_SEED_TASK_COUNT = 5


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


# PATCH /tasks/{id}/status


def test_task_status_complete_task(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    tasks = _seed_tasks(db_session, goal.id, count=1)

    resp = auth_client.patch(
        f"/tasks/{tasks[0].id}/status",
        json={"status": "completed"},
    )

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["new_status"] == "completed"


def test_task_status_invalid_status_rejected(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    tasks = _seed_tasks(db_session, goal.id, count=1)

    resp = auth_client.patch(
        f"/tasks/{tasks[0].id}/status",
        json={"status": "invalid_status"},
    )

    assert resp.status_code == HTTP_400_BAD_REQUEST


def test_task_status_task_not_found(auth_client, db_session):
    _seed_user(db_session)

    resp = auth_client.patch(
        "/tasks/999/status",
        json={"status": "completed"},
    )

    assert resp.status_code == HTTP_404_NOT_FOUND


# PATCH /tasks/{id}/notes


def test_task_notes_save_notes(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    tasks = _seed_tasks(db_session, goal.id, count=1)

    resp = auth_client.patch(
        f"/tasks/{tasks[0].id}/notes",
        json={"notes": "My progress notes"},
    )

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["notes"] == "My progress notes"


def test_task_notes_whitespace_stripped(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    tasks = _seed_tasks(db_session, goal.id, count=1)

    resp = auth_client.patch(
        f"/tasks/{tasks[0].id}/notes",
        json={"notes": "   trimmed   "},
    )

    assert resp.json()["notes"] == "trimmed"


# GET /goals/{id}/replan/check


def test_replan_check_no_missed_tasks(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session)
    _seed_tasks(db_session, goal.id, count=3, status="pending")

    resp = auth_client.get(f"/goals/{goal.id}/replan/check?threshold=3")

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["needs_replan"] is False


def test_replan_check_paused_goal_skips_replan(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="paused", paused_at=datetime(2026, 3, 20))

    resp = auth_client.get(f"/goals/{goal.id}/replan/check")

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["needs_replan"] is False
