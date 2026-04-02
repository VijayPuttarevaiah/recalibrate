"""
TDD - Tests for reminder_service.py

Covers three notification triggers:
  1. Upcoming  - due within 24 h, not completed  -> "Deadline Reminder"
  2. Overdue   - past due date, not completed     -> "Task Overdue"
  3. Completed - completed within last hour       -> "Task Completed"

DB session is patched via _create_db_session so tests never hit a real DB.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from notifications.services.reminder_service import (
    check_upcoming_deadlines,
    build_reminder_message,
    build_overdue_message,
    build_completed_message,
    REMINDER_TITLE,
    OVERDUE_TITLE,
    COMPLETED_TITLE,
    COMPLETED_STATUS,
)


# -- Helpers -------------------------------------------------------------------


def make_task(task_id, user_id, title, **overrides):
    task = MagicMock()
    task.id = task_id
    task.goal_id = overrides.get("goal_id", 1)
    task.title = title
    task.due_date = overrides.get("due_date", datetime.now() + timedelta(hours=6))
    task.status = overrides.get("status", "in_progress")
    task.updated_at = datetime.now() - timedelta(minutes=30)
    task.goal = MagicMock()
    task.goal.user_id = user_id
    return task


def make_user(user_id, email):
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


def _set_task_query_effects(mock_db, effects):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.all.side_effect = effects


def _set_user_lookup(mock_db, user):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = user


# -- Message builders ----------------------------------------------------------


def test_reminder_has_title():
    assert "Write report" in build_reminder_message("Write report")


def test_reminder_returns_string():
    assert isinstance(build_reminder_message("Task"), str)


def test_reminder_mentions_24h():
    assert "24 hours" in build_reminder_message("Task")


def test_overdue_has_title():
    assert "Submit form" in build_overdue_message("Submit form")


def test_overdue_returns_string():
    assert isinstance(build_overdue_message("Task"), str)


def test_overdue_mentions_overdue():
    assert "overdue" in build_overdue_message("Task").lower()


def test_completed_has_title():
    assert "Final exam" in build_completed_message("Final exam")


def test_completed_returns_string():
    assert isinstance(build_completed_message("Task"), str)


def test_completed_mentions_done():
    msg = build_completed_message("Task").lower()
    assert "completed" in msg or "congratulations" in msg


# -- Upcoming deadline notifications -------------------------------------------


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    upcoming = make_task(1, 1, "Task A", due_date=datetime.now() + timedelta(hours=6))
    _set_task_query_effects(mock_db, [[upcoming], [], []])
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(mock_db, [[make_task(1, 1, "Task")], [], []])
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == REMINDER_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_send_mail_true(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(mock_db, [[make_task(1, 1, "Task")], [], []])
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.send_mail is True


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_no_tasks(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(mock_db, [[], [], []])
    check_upcoming_deadlines()
    mock_create.assert_not_called()


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(mock_db, [[make_task(1, 99, "Ghost")], [], []])
    _set_user_lookup(mock_db, None)
    check_upcoming_deadlines()
    mock_create.assert_not_called()


# -- Overdue notifications -----------------------------------------------------


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    overdue = make_task(2, 1, "Late Task", due_date=datetime.now() - timedelta(hours=5))
    _set_task_query_effects(mock_db, [[], [overdue], []])
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [make_task(2, 1, "Late", due_date=datetime.now() - timedelta(hours=5))],
            [],
        ],
    )
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == OVERDUE_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_message_has_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [
                make_task(
                    2,
                    1,
                    "Submit invoice",
                    due_date=datetime.now() - timedelta(hours=5),
                )
            ],
            [],
        ],
    )
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert "Submit invoice" in params.message


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [
                make_task(
                    2,
                    99,
                    "Ghost",
                    due_date=datetime.now() - timedelta(hours=5),
                )
            ],
            [],
        ],
    )
    _set_user_lookup(mock_db, None)
    check_upcoming_deadlines()
    mock_create.assert_not_called()


# -- Completed task notifications ----------------------------------------------


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    done = make_task(3, 1, "Done Task", status=COMPLETED_STATUS)
    _set_task_query_effects(mock_db, [[], [], [done]])
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 1, "Done Task", status=COMPLETED_STATUS)],
        ],
    )
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == COMPLETED_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_message_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 1, "Write thesis", status=COMPLETED_STATUS)],
        ],
    )
    _set_user_lookup(mock_db, make_user(1, "u@e.com"))
    check_upcoming_deadlines()
    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert "Write thesis" in params.message


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 99, "Ghost", status=COMPLETED_STATUS)],
        ],
    )
    _set_user_lookup(mock_db, None)
    check_upcoming_deadlines()
    mock_create.assert_not_called()


# -- DB lifecycle --------------------------------------------------------------


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_db_closed_after_success(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    _set_task_query_effects(mock_db, [[], [], []])
    check_upcoming_deadlines()
    mock_db.close.assert_called_once()


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_db_closed_on_exception(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    mock_db.query.side_effect = Exception("DB exploded")
    check_upcoming_deadlines()  # must not raise
    mock_db.close.assert_called_once()
