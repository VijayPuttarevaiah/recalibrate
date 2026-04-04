"""Unit tests for `create_notification` in `notifications.services.notification_service`."""

from unittest.mock import patch

from notifications.services.notification_service import (
    NotificationParams,
    create_notification,
)


def test_create_adds_notification(mock_db):
    params = NotificationParams(user_id=1, title="T", message="M")
    create_notification(db=mock_db, params=params)
    mock_db.add.assert_called_once()


def test_create_commits_to_db(mock_db):
    params = NotificationParams(user_id=1, title="T", message="M")
    create_notification(db=mock_db, params=params)
    mock_db.commit.assert_called_once()


def test_create_refreshes(mock_db):
    params = NotificationParams(user_id=1, title="T", message="M")
    create_notification(db=mock_db, params=params)
    mock_db.refresh.assert_called_once()


def test_create_returns(mock_db):
    params = NotificationParams(user_id=1, title="T", message="M")
    result = create_notification(db=mock_db, params=params)
    assert result is not None


def test_create_skips_email_flag(mock_db):
    with patch(
        "notifications.services.notification_service.send_notification_email"
    ) as mock_mail:
        params = NotificationParams(user_id=1, title="T", message="M", send_mail=False)
        create_notification(db=mock_db, params=params)
        mock_mail.assert_not_called()


def test_create_no_addr(mock_db):
    with patch(
        "notifications.services.notification_service.send_notification_email"
    ) as mock_mail:
        params = NotificationParams(
            user_id=1, title="T", message="M", send_mail=True, email=None
        )
        create_notification(db=mock_db, params=params)
        mock_mail.assert_not_called()


def test_create_email_sent(mock_db):
    with patch(
        "notifications.services.notification_service.send_notification_email"
    ) as mock_mail:
        params = NotificationParams(
            user_id=1,
            title="Reminder",
            message="Do it",
            send_mail=True,
            email="u@e.com",
        )
        create_notification(db=mock_db, params=params)
        mock_mail.assert_called_once_with(email="u@e.com", title="Reminder", message="Do it")


def test_create_add_fail_none(mock_db):
    mock_db.add.side_effect = Exception("DB down")
    params = NotificationParams(user_id=1, title="T", message="M")
    result = create_notification(db=mock_db, params=params)
    assert result is None


def test_create_rolls_back(mock_db):
    mock_db.commit.side_effect = Exception("commit failed")
    params = NotificationParams(user_id=1, title="T", message="M")
    create_notification(db=mock_db, params=params)
    mock_db.rollback.assert_called_once()


def test_create_no_email_db_fail(mock_db):
    mock_db.add.side_effect = Exception("DB down")
    with patch(
        "notifications.services.notification_service.send_notification_email"
    ) as mock_mail:
        params = NotificationParams(
            user_id=1,
            title="T",
            message="M",
            send_mail=True,
            email="u@e.com",
        )
        create_notification(db=mock_db, params=params)
        mock_mail.assert_not_called()
