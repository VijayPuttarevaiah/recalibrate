"""Trigger tests for `check_upcoming_deadlines` in `notifications.services.reminder_service`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from notifications.services.reminder_service import (
    COMPLETED_STATUS,
    COMPLETED_TITLE,
    OVERDUE_TITLE,
    REMINDER_TITLE,
    check_upcoming_deadlines,
)

from notifications.tests.reminder.reminder_service_test_utils import (
    make_task,
    make_user,
    set_task_query_effects,
    set_user_lookup,
)


# Upcoming deadline notifications


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    upcoming = make_task(1, 1, "Task A", due_date=datetime.now() + timedelta(hours=6))
    set_task_query_effects(mock_db, [[upcoming], [], []])
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(mock_db, [[make_task(1, 1, "Task")], [], []])
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == REMINDER_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_send_mail_true(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(mock_db, [[make_task(1, 1, "Task")], [], []])
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.send_mail is True


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_no_tasks(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(mock_db, [[], [], []])

    check_upcoming_deadlines()

    mock_create.assert_not_called()


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_upcoming_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(mock_db, [[make_task(1, 99, "Ghost")], [], []])
    set_user_lookup(mock_db, None)

    check_upcoming_deadlines()

    mock_create.assert_not_called()


# Overdue notifications


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    overdue = make_task(2, 1, "Late Task", due_date=datetime.now() - timedelta(hours=5))
    set_task_query_effects(mock_db, [[], [overdue], []])
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
        mock_db,
        [
            [],
            [make_task(2, 1, "Late", due_date=datetime.now() - timedelta(hours=5))],
            [],
        ],
    )
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == OVERDUE_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_message_has_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
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
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert "Submit invoice" in params.message


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_overdue_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
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
    set_user_lookup(mock_db, None)

    check_upcoming_deadlines()

    mock_create.assert_not_called()


# Completed task notifications


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_creates(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    done = make_task(3, 1, "Done Task", status=COMPLETED_STATUS)
    set_task_query_effects(mock_db, [[], [], [done]])
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    assert mock_create.call_count == 1


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 1, "Done Task", status=COMPLETED_STATUS)],
        ],
    )
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert params.title == COMPLETED_TITLE


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_message_title(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 1, "Write thesis", status=COMPLETED_STATUS)],
        ],
    )
    set_user_lookup(mock_db, make_user(1, "u@e.com"))

    check_upcoming_deadlines()

    _, kwargs = mock_create.call_args
    params = kwargs["params"]
    assert "Write thesis" in params.message


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_completed_skips_no_user(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(
        mock_db,
        [
            [],
            [],
            [make_task(3, 99, "Ghost", status=COMPLETED_STATUS)],
        ],
    )
    set_user_lookup(mock_db, None)

    check_upcoming_deadlines()

    mock_create.assert_not_called()
