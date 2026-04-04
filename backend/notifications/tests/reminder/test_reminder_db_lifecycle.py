"""DB lifecycle tests for reminder notifications."""

from unittest.mock import MagicMock, patch

from notifications.services.reminder_service import check_upcoming_deadlines

from notifications.tests.reminder.reminder_service_test_utils import set_task_query_effects


@patch("notifications.services.reminder_service.create_notification")
@patch("notifications.services.reminder_service._create_db_session")
def test_db_closed_after_success(mock_session, mock_create):
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    set_task_query_effects(mock_db, [[], [], []])

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
