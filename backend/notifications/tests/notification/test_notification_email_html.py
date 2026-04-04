"""Unit tests for `build_email_html` in `notifications.services.notification_service`."""

from notifications.services.notification_service import (
    ROADMAP_URL,
    build_email_html,
)


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
