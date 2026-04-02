"""
TDD - RED phase tests for notification_service.py

Covers:
  - create_notification: happy path, email gating, DB failure rollback
  - send_notification_email: correct args forwarded to send_email
  - build_email_html: output contains required content
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from notifications.services.notification_service import (
    build_email_html,
    create_notification,
    send_notification_email,
    ROADMAP_URL,
    NotificationParams,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────
HTML_BODY_ARG_INDEX = 2


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    # refresh is a no-op by default
    db.refresh.return_value = None
    return db


# ── build_email_html ───────────────────────────────────────────────────────────


def test_email_has_title():
    html = build_email_html("My Goal", "Some message")
    assert "My Goal" in html


def test_email_has_message():
    html = build_email_html("Title", "Deadline approaching fast")
    assert "Deadline approaching fast" in html


def test_email_has_button():
    html = build_email_html("T", "M")
    assert "View My Roadmap" in html


def test_email_has_roadmap_url():
    html = build_email_html("T", "M")
    assert ROADMAP_URL in html


def test_email_returns_string():
    result = build_email_html("T", "M")
    assert isinstance(result, str)


def test_email_has_html_tag():
    html = build_email_html("T", "M")
    assert "<html>" in html and "</html>" in html


# ── send_notification_email ────────────────────────────────────────────────────


def test_send_email_recipient():
    with patch("notifications.services.notification_service.send_email") as mock_send:
        send_notification_email("user@example.com", "Title", "Msg")
        assert mock_send.call_args[0][0] == "user@example.com"


def test_send_email_calls_subject():
    with patch("notifications.services.notification_service.send_email") as mock_send:
        send_notification_email("user@example.com", "My Subject", "Msg")
        assert mock_send.call_args[0][1] == "My Subject"


def test_send_email_calls_html():
    with patch("notifications.services.notification_service.send_email") as mock_send:
        send_notification_email("u@e.com", "T", "M")
        html_body = mock_send.call_args[0][HTML_BODY_ARG_INDEX]
        assert "<html>" in html_body


def test_send_email_called_once():
    with patch("notifications.services.notification_service.send_email") as mock_send:
        send_notification_email("u@e.com", "T", "M")
        mock_send.assert_called_once()


# ── create_notification ────────────────────────────────────────────────────────


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


def test_create_no_email_send_false(mock_db):
    with patch(
        "notifications.services.notification_service.send_notification_email"
    ) as mock_mail:
        params = NotificationParams(user_id=1, title="T", message="M", send_mail=False)
        create_notification(db=mock_db, params=params)
        mock_mail.assert_not_called()


def test_create_no_email_no_addr(mock_db):
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
        mock_mail.assert_called_once_with(
            email="u@e.com", title="Reminder", message="Do it"
        )


def test_create_returns_none_on_add(mock_db):
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
