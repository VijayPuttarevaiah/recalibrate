"""Integration tests for goal pause/resume endpoints.

Split from the older monolithic `test_integration_goal_endpoints.py` to improve
DPy modularization metrics.
"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

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


# PATCH /goals/{id}/pause


def test_pause_active_goal(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="in_progress")

    resp = auth_client.patch(f"/goals/{goal.id}/pause")

    assert resp.status_code == HTTP_200_OK
    data = resp.json()
    assert data["status"] == "paused"
    assert data["goal_id"] == goal.id


def test_pause_pending_goal(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="pending")

    resp = auth_client.patch(f"/goals/{goal.id}/pause")

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["status"] == "paused"


def test_pause_completed_rejected(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="completed")

    resp = auth_client.patch(f"/goals/{goal.id}/pause")

    assert resp.status_code == HTTP_400_BAD_REQUEST


def test_pause_already_paused(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="paused", paused_at=datetime(2026, 3, 20))

    resp = auth_client.patch(f"/goals/{goal.id}/pause")

    assert resp.status_code == HTTP_400_BAD_REQUEST


def test_pause_nonexistent_goal(auth_client, db_session):
    _seed_user(db_session)

    resp = auth_client.patch("/goals/999/pause")

    assert resp.status_code == HTTP_404_NOT_FOUND


def test_pause_persists_status(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="in_progress")

    auth_client.patch(f"/goals/{goal.id}/pause")
    resp = auth_client.get("/goals/")

    assert resp.json()[0]["status"] == "paused"


# PATCH /goals/{id}/resume


def test_resume_keep_original(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="paused", paused_at=datetime(2026, 3, 20))

    with (
        patch("goals.goal.service.generate_resume_tasks") as mock_gen,
        patch("goals.goal.service.format_summary_for_llm", return_value="ctx"),
        patch(
            "goals.goal.service.build_progress_summary",
            return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 0}},
        ),
    ):
        mock_gen.return_value = [
            {"title": "New task 1", "date": str(date.today() + timedelta(days=1))},
        ]
        resp = auth_client.patch(
            f"/goals/{goal.id}/resume",
            json={"mode": "keep_original"},
        )

    assert resp.status_code == HTTP_200_OK
    data = resp.json()
    assert data["status"] == "in_progress"
    assert data["adjusted"] is True


def test_resume_new_end_date(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="paused", paused_at=datetime(2026, 3, 20))

    new_date = str(date.today() + timedelta(days=30))
    with (
        patch("goals.goal.service.generate_resume_tasks") as mock_gen,
        patch("goals.goal.service.format_summary_for_llm", return_value="ctx"),
        patch(
            "goals.goal.service.build_progress_summary",
            return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 0}},
        ),
    ):
        mock_gen.return_value = [{"title": "Task", "date": new_date}]
        resp = auth_client.patch(
            f"/goals/{goal.id}/resume",
            json={"mode": "new_end_date", "new_end_date": new_date},
        )

    assert resp.status_code == HTTP_200_OK
    assert resp.json()["new_end_date"] == new_date


def test_resume_non_paused(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="in_progress")

    resp = auth_client.patch(
        f"/goals/{goal.id}/resume",
        json={"mode": "keep_original"},
    )

    assert resp.status_code == HTTP_400_BAD_REQUEST


def test_resume_missing_body(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="paused", paused_at=datetime(2026, 3, 20))

    resp = auth_client.patch(f"/goals/{goal.id}/resume")

    assert resp.status_code == HTTP_422_UNPROCESSABLE_ENTITY


# End-to-end flow


def test_full_pause_resume_cycle(auth_client, db_session):
    _seed_user(db_session)
    goal = _seed_goal(db_session, status="in_progress")
    _seed_tasks(db_session, goal.id, count=3)

    resp = auth_client.patch(f"/goals/{goal.id}/pause")
    assert resp.json()["status"] == "paused"

    resp = auth_client.get("/goals/")
    assert resp.json()[0]["status"] == "paused"

    resp = auth_client.get(f"/goals/{goal.id}/replan/check")
    assert resp.json()["needs_replan"] is False

    with (
        patch("goals.goal.service.generate_resume_tasks") as mock_gen,
        patch("goals.goal.service.format_summary_for_llm", return_value="ctx"),
        patch(
            "goals.goal.service.build_progress_summary",
            return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 3}},
        ),
    ):
        mock_gen.return_value = [
            {
                "title": "Resumed task",
                "date": str(date.today() + timedelta(days=1)),
            },
        ]
        resp = auth_client.patch(
            f"/goals/{goal.id}/resume",
            json={"mode": "keep_original"},
        )
        assert resp.json()["status"] == "in_progress"

        resp = auth_client.get("/goals/")
        assert resp.json()[0]["status"] == "in_progress"
