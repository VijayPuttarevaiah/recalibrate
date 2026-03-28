import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from services.reminder_service import check_upcoming_deadlines


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_task(id, user_id, title, due_date=None):
    task = MagicMock()
    task.id = id
    task.user_id = user_id
    task.title = title
    task.due_date = due_date or datetime.now() + timedelta(hours=12)
    task.status = "in_progress"
    return task


def make_user(id, email):
    user = MagicMock()
    user.id = id
    user.email = email
    return user


# ── check_upcoming_deadlines ───────────────────────────────────────────────────

class TestCheckUpcomingDeadlines:

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_creates_notification_for_each_upcoming_task(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        tasks = [make_task(1, 10, "Write report"), make_task(2, 11, "Submit form")]
        mock_db.query.return_value.filter.return_value.all.return_value = tasks

        def user_query_side_effect(model):
            q = MagicMock()
            q.filter.return_value.first.side_effect = [
                make_user(10, "a@x.com"),
                make_user(11, "b@x.com"),
            ]
            return q

        mock_db.query.side_effect = user_query_side_effect
        # Reset to normal for Task query
        mock_db.query.side_effect = None
        mock_db.query.return_value.filter.return_value.all.return_value = tasks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            make_user(10, "a@x.com"),
            make_user(11, "b@x.com"),
        ]

        check_upcoming_deadlines()
        assert mock_create.call_count == 2

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_sends_email_flag_true_in_notification(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        task = make_task(1, 10, "Submit assignment")
        mock_db.query.return_value.filter.return_value.all.return_value = [task]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(10, "u@x.com")

        check_upcoming_deadlines()

        _, kwargs = mock_create.call_args
        assert kwargs.get("send_mail") is True

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_no_notifications_when_no_tasks(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        check_upcoming_deadlines()
        mock_create.assert_not_called()

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_skips_task_when_user_not_found(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 99, "Ghost task")]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        check_upcoming_deadlines()
        mock_create.assert_not_called()

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_db_closed_after_execution(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        check_upcoming_deadlines()
        mock_db.close.assert_called_once()

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_db_closed_even_on_exception(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.side_effect = Exception("DB exploded")

        check_upcoming_deadlines()  # should not raise
        mock_db.close.assert_called_once()

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_notification_title_is_deadline_reminder(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "My Task")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")

        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert kwargs.get("title") == "Deadline Reminder"

    @patch("services.reminder_service.SessionLocal")
    @patch("services.reminder_service.NotificationService.create_notification")
    def test_notification_message_contains_task_title(self, mock_create, mock_session):
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [make_task(1, 1, "Write thesis")]
        mock_db.query.return_value.filter.return_value.first.return_value = make_user(1, "u@e.com")

        check_upcoming_deadlines()
        _, kwargs = mock_create.call_args
        assert "Write thesis" in kwargs.get("message", "")