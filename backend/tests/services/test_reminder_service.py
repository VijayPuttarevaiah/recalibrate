"""
TDD - Tests for reminder_service.py

Covers three notification triggers:
  1. Upcoming  - due within 24 h, not completed  -> "Deadline Reminder"
  2. Overdue   - past due date, not completed     -> "Task Overdue"
  3. Completed - completed within last hour       -> "Task Completed"

DB session is patched via _create_db_session so tests never hit a real DB.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from services.reminder_service import (
    check_upcoming_deadlines,
    _build_reminder_message,
    _build_overdue_message,
    _build_completed_message,
    REMINDER_TITLE,
    OVERDUE_TITLE,
    COMPLETED_TITLE,
    COMPLETED_STATUS,
)


# -- Helpers -------------------------------------------------------------------

def make_task(task_id, user_id, title, due_date=None, status="in_progress", goal_id=1):
    task = MagicMock()
    task.id = task_id
    task.goal_id = goal_id
    task.title = title
    task.due_date = due_date or datetime.now() + timedelta(hours=6)
    task.status = status
    task.updated_at = datetime.now() - timedelta(minutes=30)
    task.goal = MagicMock()
    task.goal.user_id = user_id
    return task


def make_user(user_id, email):
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


# -- Message builders ----------------------------------------------------------

class TestBuildReminderMessage:
    def test_contains_task_title(self):
        assert "Write report" in _build_reminder_message("Write report")

    def test_returns_string(self):
        assert isinstance(_build_reminder_message("Task"), str)

    def test_mentions_24_hours(self):
        assert "24 hours" in _build_reminder_message("Task")


class TestBuildOverdueMessage:
    def test_contains_task_title(self):
        assert "Submit form" in _build_overdue_message("Submit form")

    def test_returns_string(self):
        assert isinstance(_build_overdue_message("Task"), str)

    def test_mentions_overdue(self):
        assert "overdue" in _build_overdue_message("Task").lower()


class TestBuildCompletedMessage:
    def test_contains_task_title(self):
        assert "Final exam" in _build_completed_message("Final exam")

    def test_returns_string(self):
        assert isinstance(_build_completed_message("Task"), str)

    def test_mentions_completed_or_congratulations(self):
        msg = _build_completed_message("Task").lower()
        assert "completed" in msg or "congratulations" in msg


# -- Upcoming deadline notifications -------------------------------------------

class TestUpcomingDeadlineNotifications:

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_creates_notification_for_upcoming_task(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        upcoming = make_task(1, 1, "Task A", due_date=datetime.now() + timedelta(hours=6))
        mock_db.query.return_value.filter.return_value.all.side_effect = [[upcoming], [], []]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        assert mock_create.call_count == 1

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_upcoming_notification_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [[make_task(1, 1, "Task")], [], []]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert params.title == REMINDER_TITLE

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_upcoming_notification_send_mail_true(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [[make_task(1, 1, "Task")], [], []]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert params.send_mail is True

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_no_notification_when_no_tasks(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], [], []]
        check_upcoming_deadlines()
        mock_create.assert_not_called()

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_skips_when_user_not_found(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [[make_task(1, 99, "Ghost")], [], []]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        check_upcoming_deadlines()
        mock_create.assert_not_called()


# -- Overdue notifications -----------------------------------------------------

class TestOverdueNotifications:

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_creates_notification_for_overdue_task(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        overdue = make_task(2, 1, "Late Task", due_date=datetime.now() - timedelta(hours=5))
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], [overdue], []]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        assert mock_create.call_count == 1

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_overdue_notification_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [make_task(2, 1, "Late", due_date=datetime.now() - timedelta(hours=5))], []
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert params.title == OVERDUE_TITLE

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_overdue_message_contains_task_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [make_task(2, 1, "Submit invoice", due_date=datetime.now() - timedelta(hours=5))], []
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert "Submit invoice" in params.message

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_skips_overdue_when_user_not_found(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [make_task(2, 99, "Ghost", due_date=datetime.now() - timedelta(hours=5))], []
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        check_upcoming_deadlines()
        mock_create.assert_not_called()


# -- Completed task notifications ----------------------------------------------

class TestCompletedTaskNotifications:

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_creates_notification_for_completed_task(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        done = make_task(3, 1, "Done Task", status=COMPLETED_STATUS)
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], [], [done]]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        assert mock_create.call_count == 1

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_completed_notification_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [], [make_task(3, 1, "Done Task", status=COMPLETED_STATUS)]
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert params.title == COMPLETED_TITLE

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_completed_message_contains_task_title(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [], [make_task(3, 1, "Write thesis", status=COMPLETED_STATUS)]
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")
        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        params = kwargs["params"]
        assert "Write thesis" in params.message

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_skips_completed_when_user_not_found(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [], [], [make_task(3, 99, "Ghost", status=COMPLETED_STATUS)]
        ]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        check_upcoming_deadlines()
        mock_create.assert_not_called()


# -- DB lifecycle --------------------------------------------------------------

class TestDbLifecycle:

    @patch("services.reminder_service.create_notification")
    @patch("services.reminder_service._create_db_session")
    def test_db_closed_after_success(self, mock_session, mock_create):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], [], []]
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