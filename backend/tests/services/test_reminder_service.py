"""
TDD - RED phase tests for reminder_service.py

Covers:
  - _build_reminder_message: output correctness
  - check_upcoming_deadlines: notification dispatch, user-not-found guard,
    DB always closed, exception safety

Note: We patch `_create_db_session` (the thin wrapper in reminder_service)
so tests never touch the real DBSession singleton or database.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from services.reminder_service import (
    check_upcoming_deadlines,
    _build_reminder_message,
    REMINDER_TITLE,
    COMPLETED_STATUS,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_task(task_id: int, user_id: int, title: str):
    task = MagicMock()
    task.id = task_id
    task.user_id = user_id
    task.title = title
    task.due_date = datetime.now() + timedelta(hours=6)
    task.status = "in_progress"
    return task


def make_user(user_id: int, email: str):
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


# ── _build_reminder_message ────────────────────────────────────────────────────

class TestBuildReminderMessage:

    def test_contains_task_title(self):
        msg = _build_reminder_message("Write report")
        assert "Write report" in msg

    def test_returns_string(self):
        assert isinstance(_build_reminder_message("Task"), str)

    def test_message_mentions_24_hours(self):
        msg = _build_reminder_message("Task")
        assert "24 hours" in msg


# ── check_upcoming_deadlines ───────────────────────────────────────────────────

class TestCheckUpcomingDeadlines:

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_creates_notification_for_each_task(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        tasks = [make_task(1, 10, "Task A"), make_task(2, 11, "Task B")]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            make_user(10, "a@x.com"),
            make_user(11, "b@x.com"),
        ]
        check_upcoming_deadlines()
        assert mock_create.call_count == 2

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_notification_uses_correct_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "My Task")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert kwargs["title"] == REMINDER_TITLE

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_notification_message_contains_task_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "Submit thesis")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert "Submit thesis" in kwargs["message"]

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_send_mail_is_true(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "Task")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert kwargs["send_mail"] is True

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_correct_email_passed_to_notification(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "Task")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "specific@email.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert kwargs["email"] == "specific@email.com"

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_no_notifications_when_no_tasks(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        check_upcoming_deadlines()
        mock_create.assert_not_called()

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_skips_task_when_user_not_found(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 99, "Orphan task")]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        check_upcoming_deadlines()
        mock_create.assert_not_called()

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_db_closed_after_success(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        check_upcoming_deadlines()
        mock_db.close.assert_called_once()

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_db_closed_even_when_exception_raised(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.side_effect = Exception("DB exploded")
        check_upcoming_deadlines()  # must not raise
        mock_db.close.assert_called_once()