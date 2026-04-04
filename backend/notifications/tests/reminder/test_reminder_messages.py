"""Message-builder unit tests for `notifications.services.reminder_service`."""

from notifications.services.reminder_service import (
    build_completed_message,
    build_overdue_message,
    build_reminder_message,
)


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
