"""

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


def _set_notifications_return(mock_db, notifications):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = notifications


def _set_first_notification(mock_db, notification):
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = notification


# ── GET /notifications/{user_id} ───────────────────────────────────────────────


def test_get_returns_200_ok(client, mock_db):
    _set_notifications_return(mock_db, [])
    response = client.get(f"/notifications/{DEFAULT_USER_ID}")
    assert response.status_code == HTTP_OK


def test_get_success_field_is_true(client, mock_db):
    _set_notifications_return(mock_db, [])
    response = client.get(f"/notifications/{DEFAULT_USER_ID}")
    assert response.json()["success"] is True


def test_get_returns_empty_list(client, mock_db):
    _set_notifications_return(mock_db, [])
    response = client.get(f"/notifications/{NO_NOTIFICATIONS_USER_ID}")
    assert response.json()["data"] == []


def test_get_returns_notifications(client, mock_db):
    _set_notifications_return(
        mock_db,
        [
            _make_notification(DEFAULT_NOTIFICATION_ID, ALT_USER_ID),
            _make_notification(SECOND_NOTIFICATION_ID, ALT_USER_ID),
        ],
    )
    response = client.get(f"/notifications/{ALT_USER_ID}")
    assert len(response.json()["data"]) == EXPECTED_NOTIFICATIONS_COUNT


def test_get_notification_user_id(client, mock_db):
    _set_notifications_return(
        mock_db,
        [_make_notification(DEFAULT_NOTIFICATION_ID, OTHER_USER_ID)],
    )
    response = client.get(f"/notifications/{OTHER_USER_ID}")
    assert response.json()["data"][0]["user_id"] == OTHER_USER_ID


def test_get_notification_fields(client, mock_db):
    _set_notifications_return(
        mock_db,
        [_make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID)],
    )
    data = client.get(f"/notifications/{DEFAULT_USER_ID}").json()["data"][0]
    for field in ("id", "user_id", "title", "message", "is_read", "created_at"):
        assert field in data


# ── PATCH /notifications/{notification_id}/read ────────────────────────────────


def test_mark_read_200(client, mock_db):
    _set_first_notification(
        mock_db,
        _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID),
    )
    response = client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
    assert response.status_code == HTTP_OK


def test_mark_read_sets_read(client, mock_db):
    notif = _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID, is_read=False)
    _set_first_notification(mock_db, notif)
    client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
    assert notif.is_read is True


def test_mark_read_commits(client, mock_db):
    _set_first_notification(
        mock_db,
        _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID),
    )
    client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
    mock_db.commit.assert_called_once()


def test_mark_read_success_true(client, mock_db):
    _set_first_notification(
        mock_db,
        _make_notification(DEFAULT_NOTIFICATION_ID, DEFAULT_USER_ID),
    )
    response = client.patch(f"/notifications/{DEFAULT_NOTIFICATION_ID}/read")
    assert response.json()["success"] is True


def test_mark_read_404(client, mock_db):
    _set_first_notification(mock_db, None)
    response = client.patch(f"/notifications/{MISSING_NOTIFICATION_ID}/read")
    assert response.status_code == HTTP_NOT_FOUND


def test_mark_read_404_detail(client, mock_db):
    _set_first_notification(mock_db, None)
    response = client.patch(f"/notifications/{MISSING_NOTIFICATION_ID}/read")
    assert "not found" in response.json()["detail"].lower()
