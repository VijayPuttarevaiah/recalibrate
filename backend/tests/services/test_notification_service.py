import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime
from sqlalchemy.orm import Session

from services.notification_service import NotificationService
from models.notification import Notification


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def sample_notification():
    notif = Notification()
    notif.id = 1
    notif.user_id = 42
    notif.title = "Test Title"
    notif.message = "Test message body"
    notif.is_read = False
    notif.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return notif


# ── create_notification ────────────────────────────────────────────────────────

class TestCreateNotification:

    def test_saves_notification_to_db(self, mock_db, sample_notification):
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)
        result = NotificationService.create_notification(
            mock_db, user_id=42, title="Test Title", message="Test message body"
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_returns_notification_object(self, mock_db, sample_notification):
        mock_db.refresh.side_effect = lambda obj: None
        result = NotificationService.create_notification(
            mock_db, user_id=42, title="Title", message="Msg"
        )
        assert result is not None

    def test_no_email_sent_when_send_mail_false(self, mock_db):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.create_notification(
                mock_db, user_id=1, title="T", message="M", send_mail=False
            )
            mock_email.assert_not_called()

    def test_no_email_sent_when_email_is_none(self, mock_db):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.create_notification(
                mock_db, user_id=1, title="T", message="M",
                send_mail=True, email=None
            )
            mock_email.assert_not_called()

    def test_email_sent_when_send_mail_true_and_email_provided(self, mock_db):
        with patch.object(NotificationService, "send_email_notification") as mock_mail:
            NotificationService.create_notification(
                mock_db, user_id=1, title="Reminder", message="Do the thing",
                send_mail=True, email="user@example.com"
            )
            mock_mail.assert_called_once_with("user@example.com", "Reminder", "Do the thing")

    def test_returns_none_on_db_exception(self, mock_db):
        mock_db.add.side_effect = Exception("DB is down")
        result = NotificationService.create_notification(
            mock_db, user_id=1, title="T", message="M"
        )
        assert result is None
        mock_db.rollback.assert_called_once()

    def test_rollback_called_on_exception(self, mock_db):
        mock_db.commit.side_effect = Exception("Commit failed")
        NotificationService.create_notification(mock_db, user_id=1, title="T", message="M")
        mock_db.rollback.assert_called_once()


# ── send_email_notification ────────────────────────────────────────────────────

class TestSendEmailNotification:

    def test_calls_send_email_with_correct_address(self):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.send_email_notification(
                "test@example.com", "My Title", "My Message"
            )
            assert mock_email.call_args[0][0] == "test@example.com"

    def test_calls_send_email_with_correct_subject(self):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.send_email_notification(
                "test@example.com", "My Title", "My Message"
            )
            assert mock_email.call_args[0][1] == "My Title"

    def test_email_html_contains_title(self):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.send_email_notification(
                "u@e.com", "Goal Achieved!", "You did it"
            )
            html_body = mock_email.call_args[0][2]
            assert "Goal Achieved!" in html_body

    def test_email_html_contains_message(self):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.send_email_notification(
                "u@e.com", "Title", "You have a deadline soon"
            )
            html_body = mock_email.call_args[0][2]
            assert "You have a deadline soon" in html_body

    def test_email_html_contains_view_roadmap_button(self):
        with patch("services.notification_service.send_email") as mock_email:
            NotificationService.send_email_notification("u@e.com", "T", "M")
            html_body = mock_email.call_args[0][2]
            assert "View My Roadmap" in html_body