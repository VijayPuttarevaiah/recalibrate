"""
TDD - RED phase tests for routers/notifications.py

Covers:
  - GET /notifications/{user_id}  → list, empty list, success flag
  - PATCH /notifications/{id}/read → marks read, 404 on missing
"""
import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from main import app
from core.db_session import get_db

HTTP_OK = 200
HTTP_NOT_FOUND = 404

DEFAULT_USER_ID = 1
ALT_USER_ID = 5
OTHER_USER_ID = 7
NO_NOTIFICATIONS_USER_ID = 99
DEFAULT_NOTIFICATION_ID = 1
SECOND_NOTIFICATION_ID = 2
MISSING_NOTIFICATION_ID = 999
EXPECTED_NOTIFICATIONS_COUNT = 2


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
    """
    Return a SimpleNamespace that jsonable_encoder can serialize cleanly.
    MagicMock(spec=Notification) causes recursion inside jsonable_encoder
    due to SQLAlchemy internals, so we use SimpleNamespace instead.
    """
    return SimpleNamespace(
        id=notif_id,
        user_id=user_id,
        title="Test Notification",
        message="Task due soon",
        is_read=is_read,
        created_at=datetime(2026, 1, 15, 10, 0, 0),
    )


# ── GET /notifications/{user_id} ───────────────────────────────────────────────

class TestGetUserNotifications:

    def test_returns_200_ok(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get(f"/notifications/{DEFAULT_USER_ID}")
        assert response.status_code == HTTP_OK

    def test_success_field_is_true(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get(f"/notifications/{DEFAULT_USER_ID}")
        assert response.json()["success"] is True

    def test_returns_empty_list_when_no_notifications(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = []
        response = client.get(f"/notifications/{NO_NOTIFICATIONS_USER_ID}")
        assert response.json()["data"] == []

    def test_returns_notifications_for_user(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [
                _make_notification(DEFAULT_NOTIFICATION_ID, ALT_USER_ID),
                _make_notification(SECOND_NOTIFICATION_ID, ALT_USER_ID),
            ]
        response = client.get(f"/notifications/{ALT_USER_ID}")
        assert len(response.json()["data"]) == EXPECTED_NOTIFICATIONS_COUNT

    def test_notification_user_id_matches_request(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [_make_notification(DEFAULT_NOTIFICATION_ID, OTHER_USER_ID)]
        response = client.get(f"/notifications/{OTHER_USER_ID}")
        assert response.json()["data"][0]["user_id"] == OTHER_USER_ID

    def test_notification_has_expected_fields(self, client, mock_db):
        mock_db.query.return_value.filter.return_value \
            .order_by.return_value.all.return_value = [_make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID)]
        data = client.get(f"/notifications/{DEFAULT_USER_ID}").json()["data"][0]
        for field in ("id", "user_id", "title", "message", "is_read", "created_at"):
            assert field in data


# ── PATCH /notifications/{notification_id}/read ────────────────────────────────

class TestMarkAsRead:

    def test_returns_200_when_notification_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID)
        response = client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
        assert response.status_code == HTTP_OK

    def test_sets_is_read_to_true(self, client, mock_db):
        notif = _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID, is_read=False)
        mock_db.query.return_value.filter.return_value.first.return_value = notif
        client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
        assert notif.is_read is True

    def test_commits_after_marking_read(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID)
        client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
        mock_db.commit.assert_called_once()

    def test_success_field_is_true(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = \
            _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID)
        response = client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
        assert response.json()["success"] is True

    def test_returns_404_when_notification_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.patch(f"/notifications/{MISSING_NOTIFICATION_ID}/read")
        assert response.status_code == HTTP_NOT_FOUND

    def test_404_detail_message(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.patch(f"/notifications/{MISSING_NOTIFICATION_ID}/read")
        assert "not found" in response.json()["detail"].lower()