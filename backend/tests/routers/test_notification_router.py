"""
TDD - RED phase tests for routers/notifications.py

Covers:
  - GET /notifications/{user_id}  → list, empty list, success flag
  - PATCH /notifications/{id}/read → marks read, 404 on missing
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from models.notification import Notification
from utils.db_session import get_db


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _make_notification(notif_id: int, user_id: int, is_read: bool = False):
    """Return a MagicMock that mimics a Notification ORM object."""
    n = MagicMock(spec=Notification)
    n.id = notif_id
    n.user_id = user_id
    n.title = "Test Notification"
    n.message = "Task due soon"
    n.is_read = is_read
    n.created_at = datetime(2026, 1, 15, 10, 0, 0)
    return n


# ── GET /notifications/{user_id} ───────────────────────────────────────────────

class TestGetUserNotifications:

    def test_returns_200_ok(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/1")
        assert response.status_code == 200

    def test_success_field_is_true(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/1")
        assert response.json()["success"] is True

    def test_returns_empty_list_when_no_notifications(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/99")
        assert response.json()["data"] == []

    def test_returns_notifications_for_user(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [
                _make_notification(1, 5),
                _make_notification(2, 5),
            ]
        response = client.get("/notifications/5")
        assert len(response.json()["data"]) == 2

    def test_notification_user_id_matches_request(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [_make_notification(1, 7)]
        response = client.get("/notifications/7")
        assert response.json()["data"][0]["user_id"] == 7

    def test_notification_has_expected_fields(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [_make_notification(1, 1)]
        data = client.get("/notifications/1").json()["data"][0]
        for field in ("id", "user_id", "title", "message", "is_read", "created_at"):
            assert field in data


# ── PATCH /notifications/{notification_id}/read ────────────────────────────────

class TestMarkAsRead:

    def test_returns_200_when_notification_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(1, 1)
        response = client.patch("/notifications/1/read")
        assert response.status_code == 200

    def test_sets_is_read_to_true(self, client, mock_db):
        notif = _make_notification(1, 1, is_read=False)
        mock_db.query.return_value.filter.return_value.first.return_value = notif
        client.patch("/notifications/1/read")
        assert notif.is_read is True

    def test_commits_after_marking_read(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(1, 1)
        client.patch("/notifications/1/read")
        mock_db.commit.assert_called_once()

    def test_success_field_is_true(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(1, 1)
        response = client.patch("/notifications/1/read")
        assert response.json()["success"] is True

    def test_returns_404_when_notification_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.patch("/notifications/999/read")
        assert response.status_code == 404

    def test_404_detail_message(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.patch("/notifications/999/read")
        assert "not found" in response.json()["detail"].lower()