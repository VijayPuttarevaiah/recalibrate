import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime

from main import app
from utils.db_session import get_db
from models.notification import Notification


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_notif(id, user_id, is_read=False):
    n = MagicMock(spec=Notification)
    n.id = id
    n.user_id = user_id
    n.title = "Reminder"
    n.message = "Task due soon"
    n.is_read = is_read
    n.created_at = datetime(2026, 1, 1)
    return n


# ── GET /notifications/{user_id} ───────────────────────────────────────────────

class TestGetUserNotifications:

    def test_returns_200_for_valid_user(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/1")
        assert response.status_code == 200

    def test_returns_empty_list_for_user_with_no_notifications(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/99")
        assert response.json()["data"] == []

    def test_returns_notifications_for_user(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [make_notif(1, 5)]
        response = client.get("/notifications/5")
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["user_id"] == 5

    def test_response_success_field_is_true(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get("/notifications/1")
        assert response.json()["success"] is True


# ── PATCH /notifications/{id}/read ────────────────────────────────────────────

class TestMarkAsRead:

    def test_returns_200_when_notification_exists(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = make_notif(1, 1)
        response = client.patch("/notifications/1/read")
        assert response.status_code == 200

    def test_sets_is_read_to_true(self, client, mock_db):
        notif = make_notif(1, 1, is_read=False)
        mock_db.query.return_value.filter.return_value.first.return_value = notif
        client.patch("/notifications/1/read")
        assert notif.is_read is True

    def test_calls_db_commit(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = make_notif(1, 1)
        client.patch("/notifications/1/read")
        mock_db.commit.assert_called_once()

    def test_returns_404_when_notification_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.patch("/notifications/999/read")
        assert response.status_code == 404