"""
TDD - RED phase tests for notification_service.py

Covers:
  - create_notification: happy path, email gating, DB failure rollback
  - send_notification_email: correct args forwarded to send_email
  - build_email_html: output contains required content
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Session

from notifications.services.notification_service import (
    build_email_html,
    create_notification,
    send_notification_email,
    ROADMAP_URL,
    NotificationParams,
)
from notifications.models.notification import Notification


# ── Fixtures ───────────────────────────────────────────────────────────────────
HTML_BODY_ARG_INDEX = 2

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    # refresh is a no-op by default
    db.refresh.return_value = None
    return db


# ── build_email_html ───────────────────────────────────────────────────────────

class TestBuildEmailHtml:

    def test_contains_title(self):
        html = build_email_html("My Goal", "Some message")
        assert "My Goal" in html

    def test_contains_message(self):
        html = build_email_html("Title", "Deadline approaching fast")
        assert "Deadline approaching fast" in html

    def test_contains_view_roadmap_button_text(self):
        html = build_email_html("T", "M")
        assert "View My Roadmap" in html

    def test_contains_roadmap_url(self):
        html = build_email_html("T", "M")
        assert ROADMAP_URL in html

    def test_returns_string(self):
        result = build_email_html("T", "M")
        assert isinstance(result, str)

    def test_html_tag_present(self):
        html = build_email_html("T", "M")
        assert "<html>" in html and "</html>" in html


# ── send_notification_email ────────────────────────────────────────────────────

class TestSendNotificationEmail:

    def test_calls_send_email_with_correct_recipient(self):
        with patch("notifications.services.notification_service.send_email") as mock_send:
            send_notification_email("user@example.com", "Title", "Msg")
            assert mock_send.call_args[0][0] == "user@example.com"

    def test_calls_send_email_with_correct_subject(self):
        with patch("notifications.services.notification_service.send_email") as mock_send:
            send_notification_email("user@example.com", "My Subject", "Msg")
            assert mock_send.call_args[0][1] == "My Subject"

    def test_calls_send_email_with_html_body(self):
        with patch("notifications.services.notification_service.send_email") as mock_send:
            send_notification_email("u@e.com", "T", "M")
            html_body = mock_send.call_args[0][HTML_BODY_ARG_INDEX]
            assert "<html>" in html_body

    def test_send_email_called_exactly_once(self):
        with patch("notifications.services.notification_service.send_email") as mock_send:
            send_notification_email("u@e.com", "T", "M")
            mock_send.assert_called_once()


# ── create_notification ────────────────────────────────────────────────────────

class TestCreateNotification:

    def test_adds_notification_to_db(self, mock_db):
        params = NotificationParams(user_id=1, title="T", message="M")
        create_notification(db=mock_db, params=params)
        mock_db.add.assert_called_once()

    def test_commits_to_db(self, mock_db):
        params = NotificationParams(user_id=1, title="T", message="M")
        create_notification(db=mock_db, params=params)
        mock_db.commit.assert_called_once()

    def test_refreshes_after_commit(self, mock_db):
        params = NotificationParams(user_id=1, title="T", message="M")
        create_notification(db=mock_db, params=params)
        mock_db.refresh.assert_called_once()

    def test_returns_notification_instance(self, mock_db):
        params = NotificationParams(user_id=1, title="T", message="M")
        result = create_notification(db=mock_db, params=params)
        assert result is not None

    def test_no_email_when_send_mail_false(self, mock_db):
        with patch("notifications.services.notification_service.send_notification_email") as mock_mail:
            params = NotificationParams(user_id=1, title="T", message="M", send_mail=False)
            create_notification(db=mock_db, params=params)
            mock_mail.assert_not_called()

    def test_no_email_when_email_is_none(self, mock_db):
        with patch("notifications.services.notification_service.send_notification_email") as mock_mail:
            params = NotificationParams(user_id=1, title="T", message="M", send_mail=True, email=None)
            create_notification(db=mock_db, params=params)
            mock_mail.assert_not_called()

    def test_email_sent_when_send_mail_true_and_email_given(self, mock_db):
        with patch("notifications.services.notification_service.send_notification_email") as mock_mail:
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

    def test_returns_none_on_db_add_exception(self, mock_db):
        mock_db.add.side_effect = Exception("DB down")
        params = NotificationParams(user_id=1, title="T", message="M")
        result = create_notification(db=mock_db, params=params)
        assert result is None

    def test_rollback_called_on_exception(self, mock_db):
        mock_db.commit.side_effect = Exception("commit failed")
        params = NotificationParams(user_id=1, title="T", message="M")
        create_notification(db=mock_db, params=params)
        mock_db.rollback.assert_called_once()

    def test_no_email_sent_when_db_fails(self, mock_db):
        mock_db.add.side_effect = Exception("DB down")
        with patch("notifications.services.notification_service.send_notification_email") as mock_mail:
            params = NotificationParams(
                user_id=1,
                title="T",
                message="M",
                send_mail=True,
                email="u@e.com",
            )
            create_notification(db=mock_db, params=params)
            mock_mail.assert_not_called()
