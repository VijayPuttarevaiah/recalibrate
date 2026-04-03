"""Integration tests for goal endpoints using TestClient with in-memory DB."""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from auth.models.user_models import User
from goals.models.goal_models import Goal
from goals.models.task_models import Task


def _seed_user(db):
    user = User(id=1, first_name="Test", last_name="User",
                email="test@example.com", password="x", is_verified=True)
    db.add(user)
    db.commit()
    return user


def _seed_goal(db, status="in_progress", end_date=None, paused_at=None):
    goal = Goal(
        user_id=1, title="Learn Python", category="learning",
        start_date=date(2026, 1, 1),
        end_date=end_date or date(2026, 12, 31),
        status=status, paused_at=paused_at,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _seed_tasks(db, goal_id, count=5, status="pending"):
    tasks = []
    for i in range(count):
        task = Task(
            goal_id=goal_id, title=f"Task {i+1}",
            due_date=date.today() + timedelta(days=i+1), status=status,
        )
        db.add(task)
        tasks.append(task)
    db.commit()
    return tasks


class TestGoalListEndpoint:
    """GET /goals/ returns user's goals."""

    def test_returns_empty_list(self, auth_client, db_session):
        _seed_user(db_session)
        resp = auth_client.get("/goals/")
        assert resp.status_code == HTTP_200_OK
        assert resp.json() == []

    def test_returns_goals_with_task_count(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        _seed_tasks(db_session, goal.id, count=3)

        resp = auth_client.get("/goals/")
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Learn Python"
        assert data[0]["task_count"] == 3
        assert data[0]["status"] == "in_progress"

    def test_returns_paused_at_field(self, auth_client, db_session):
        _seed_user(db_session)
        now = datetime(2026, 3, 20, 10, 0, 0)
        _seed_goal(db_session, status="paused", paused_at=now)

        resp = auth_client.get("/goals/")
        data = resp.json()
        assert data[0]["status"] == "paused"
        assert data[0]["paused_at"] is not None


class TestGoalTasksEndpoint:
    """GET /goals/{id}/tasks returns goal with task list."""

    def test_returns_goal_with_tasks(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        _seed_tasks(db_session, goal.id, count=2)

        resp = auth_client.get(f"/goals/{goal.id}/tasks")
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert data["title"] == "Learn Python"
        assert len(data["tasks"]) == 2

    def test_returns_404_for_missing_goal(self, auth_client, db_session):
        _seed_user(db_session)
        resp = auth_client.get("/goals/999/tasks")
        assert resp.status_code == HTTP_404_NOT_FOUND


class TestPauseGoalEndpoint:
    """PATCH /goals/{id}/pause pauses an active goal."""

    def test_pause_active_goal(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="in_progress")

        resp = auth_client.patch(f"/goals/{goal.id}/pause")
        assert resp.status_code == HTTP_200_OK
        data = resp.json()
        assert data["status"] == "paused"
        assert data["goal_id"] == goal.id

    def test_pause_pending_goal(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="pending")

        resp = auth_client.patch(f"/goals/{goal.id}/pause")
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["status"] == "paused"

    def test_pause_completed_goal_rejected(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="completed")

        resp = auth_client.patch(f"/goals/{goal.id}/pause")
        assert resp.status_code == HTTP_400_BAD_REQUEST

    def test_pause_already_paused_rejected(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="paused",
                          paused_at=datetime(2026, 3, 20))

        resp = auth_client.patch(f"/goals/{goal.id}/pause")
        assert resp.status_code == HTTP_400_BAD_REQUEST

    def test_pause_nonexistent_goal(self, auth_client, db_session):
        _seed_user(db_session)
        resp = auth_client.patch("/goals/999/pause")
        assert resp.status_code == HTTP_404_NOT_FOUND

    def test_goal_status_persisted_after_pause(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="in_progress")

        auth_client.patch(f"/goals/{goal.id}/pause")
        resp = auth_client.get("/goals/")
        assert resp.json()[0]["status"] == "paused"


class TestResumeGoalEndpoint:
    """PATCH /goals/{id}/resume resumes a paused goal."""

    def test_resume_keep_original(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="paused",
                          paused_at=datetime(2026, 3, 20))

        with patch("goals.goal.service.generate_resume_tasks") as mock_gen, \
             patch("goals.goal.service.format_summary_for_llm", return_value="ctx"), \
             patch("goals.goal.service.build_progress_summary",
                   return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 0}}):
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

    def test_resume_new_end_date(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="paused",
                          paused_at=datetime(2026, 3, 20))

        new_date = str(date.today() + timedelta(days=30))
        with patch("goals.goal.service.generate_resume_tasks") as mock_gen, \
             patch("goals.goal.service.format_summary_for_llm", return_value="ctx"), \
             patch("goals.goal.service.build_progress_summary",
                   return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 0}}):
            mock_gen.return_value = [{"title": "Task", "date": new_date}]
            resp = auth_client.patch(
                f"/goals/{goal.id}/resume",
                json={"mode": "new_end_date", "new_end_date": new_date},
            )

        assert resp.status_code == HTTP_200_OK
        assert resp.json()["new_end_date"] == new_date

    def test_resume_non_paused_rejected(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="in_progress")

        resp = auth_client.patch(
            f"/goals/{goal.id}/resume",
            json={"mode": "keep_original"},
        )
        assert resp.status_code == HTTP_400_BAD_REQUEST

    def test_resume_missing_body_rejected(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="paused",
                          paused_at=datetime(2026, 3, 20))

        resp = auth_client.patch(f"/goals/{goal.id}/resume")
        assert resp.status_code == 422


class TestTaskStatusEndpoint:
    """PATCH /tasks/{id}/status updates task status."""

    def test_complete_task(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        tasks = _seed_tasks(db_session, goal.id, count=1)

        resp = auth_client.patch(
            f"/tasks/{tasks[0].id}/status",
            json={"status": "completed"},
        )
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["new_status"] == "completed"

    def test_invalid_status_rejected(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        tasks = _seed_tasks(db_session, goal.id, count=1)

        resp = auth_client.patch(
            f"/tasks/{tasks[0].id}/status",
            json={"status": "invalid_status"},
        )
        assert resp.status_code == HTTP_400_BAD_REQUEST

    def test_task_not_found(self, auth_client, db_session):
        _seed_user(db_session)
        resp = auth_client.patch(
            "/tasks/999/status",
            json={"status": "completed"},
        )
        assert resp.status_code == HTTP_404_NOT_FOUND


class TestTaskNotesEndpoint:
    """PATCH /tasks/{id}/notes updates task notes."""

    def test_save_notes(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        tasks = _seed_tasks(db_session, goal.id, count=1)

        resp = auth_client.patch(
            f"/tasks/{tasks[0].id}/notes",
            json={"notes": "My progress notes"},
        )
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["notes"] == "My progress notes"

    def test_notes_whitespace_stripped(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        tasks = _seed_tasks(db_session, goal.id, count=1)

        resp = auth_client.patch(
            f"/tasks/{tasks[0].id}/notes",
            json={"notes": "   trimmed   "},
        )
        assert resp.json()["notes"] == "trimmed"


class TestReplanCheckEndpoint:
    """GET /goals/{id}/replan/check returns replan status."""

    def test_no_missed_tasks(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session)
        _seed_tasks(db_session, goal.id, count=3, status="pending")

        resp = auth_client.get(f"/goals/{goal.id}/replan/check?threshold=3")
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["needs_replan"] is False

    def test_paused_goal_skips_replan(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="paused",
                          paused_at=datetime(2026, 3, 20))

        resp = auth_client.get(f"/goals/{goal.id}/replan/check")
        assert resp.status_code == HTTP_200_OK
        assert resp.json()["needs_replan"] is False


class TestPauseResumeFlow:
    """End-to-end flow: create goal → pause → verify paused → resume."""

    def test_full_pause_resume_cycle(self, auth_client, db_session):
        _seed_user(db_session)
        goal = _seed_goal(db_session, status="in_progress")
        _seed_tasks(db_session, goal.id, count=3)

        resp = auth_client.patch(f"/goals/{goal.id}/pause")
        assert resp.json()["status"] == "paused"

        resp = auth_client.get("/goals/")
        assert resp.json()[0]["status"] == "paused"

        resp = auth_client.get(f"/goals/{goal.id}/replan/check")
        assert resp.json()["needs_replan"] is False

        with patch("goals.goal.service.generate_resume_tasks") as mock_gen, \
             patch("goals.goal.service.format_summary_for_llm", return_value="ctx"), \
             patch("goals.goal.service.build_progress_summary",
                   return_value={"stats": {"completed": 0, "missed": 0, "total_tasks": 3}}):
            mock_gen.return_value = [
                {"title": "Resumed task", "date": str(date.today() + timedelta(days=1))},
            ]
            resp = auth_client.patch(
                f"/goals/{goal.id}/resume",
                json={"mode": "keep_original"},
            )
            assert resp.json()["status"] == "in_progress"

            resp = auth_client.get("/goals/")
            assert resp.json()[0]["status"] == "in_progress"
