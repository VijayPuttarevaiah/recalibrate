"""Unit tests for `send_notification_email` in `notifications.services.notification_service`."""

from unittest.mock import patch

from notifications.services.notification_service import send_notification_email


HTML_BODY_ARG_INDEX = 2


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
