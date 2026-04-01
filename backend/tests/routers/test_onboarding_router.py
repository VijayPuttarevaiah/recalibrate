"""
TDD - RED phase tests for routers/onboarding_router.py

Covers:
  - POST /onboarding/preferences  → save preferences, return roadmap
  - GET  /roadmap/{user_id}       → fetch stored preferences and return roadmap
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from main import app
from utils.db_session import get_db
from models.user_preference_model import UserPreference


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_preference(user_id=1):
    pref = MagicMock(spec=UserPreference)
    pref.id = 1
    pref.user_id = user_id
    pref.interest = "coding"
    pref.experience_level = "beginner"
    pref.hours_per_week = 10
    pref.target_goal = "Get a dev job"
    return pref


VALID_PAYLOAD = {
    "user_id": 1,
    "interest": "coding",
    "experience_level": "beginner",
    "hours_per_week": 10,
    "target_goal": "Get a dev job",
}


# ── POST /onboarding/preferences ──────────────────────────────────────────────

class TestSavePreferences:

    @patch("routers.onboarding_router.PreferenceService")
    @patch("routers.onboarding_router.RoadmapService")
    def test_returns_200_on_valid_payload(self, mock_roadmap_cls, mock_pref_cls, client):
        mock_pref_cls.return_value.save_preferences.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = [
            {"phase": "Month 1", "steps": ["Step A"]}
        ]
        response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
        assert response.status_code == 200

    @patch("routers.onboarding_router.PreferenceService")
    @patch("routers.onboarding_router.RoadmapService")
    def test_response_contains_roadmap_key(self, mock_roadmap_cls, mock_pref_cls, client):
        mock_pref_cls.return_value.save_preferences.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = [
            {"phase": "Month 1", "steps": ["Step A"]}
        ]
        response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
        assert "roadmap" in response.json()

    @patch("routers.onboarding_router.PreferenceService")
    @patch("routers.onboarding_router.RoadmapService")
    def test_roadmap_is_a_list(self, mock_roadmap_cls, mock_pref_cls, client):
        mock_pref_cls.return_value.save_preferences.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = [
            {"phase": "Month 1", "steps": ["Step A"]}
        ]
        response = client.post("/onboarding/preferences", json=VALID_PAYLOAD)
        assert isinstance(response.json()["roadmap"], list)

    @patch("routers.onboarding_router.PreferenceService")
    @patch("routers.onboarding_router.RoadmapService")
    def test_calls_preference_service_save(self, mock_roadmap_cls, mock_pref_cls, client):
        mock_pref_inst = mock_pref_cls.return_value
        mock_pref_inst.save_preferences.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = []
        client.post("/onboarding/preferences", json=VALID_PAYLOAD)
        mock_pref_inst.save_preferences.assert_called_once()

    @patch("routers.onboarding_router.PreferenceService")
    @patch("routers.onboarding_router.RoadmapService")
    def test_calls_roadmap_service_generate(self, mock_roadmap_cls, mock_pref_cls, client):
        mock_pref_cls.return_value.save_preferences.return_value = make_preference()
        mock_roadmap_inst = mock_roadmap_cls.return_value
        mock_roadmap_inst.generate_roadmap.return_value = []
        client.post("/onboarding/preferences", json=VALID_PAYLOAD)
        mock_roadmap_inst.generate_roadmap.assert_called_once()

    def test_returns_422_when_missing_required_field(self, client):
        incomplete = {"user_id": 1, "interest": "coding"}
        response = client.post("/onboarding/preferences", json=incomplete)
        assert response.status_code == 422


# ── GET /roadmap/{user_id} ─────────────────────────────────────────────────────

class TestGetRoadmap:

    @patch("routers.onboarding_router.RoadmapService")
    def test_returns_200_when_preferences_found(self, mock_roadmap_cls, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = [
            {"phase": "Month 1", "steps": ["Step A"]}
        ]
        response = client.get("/roadmap/1")
        assert response.status_code == 200

    @patch("routers.onboarding_router.RoadmapService")
    def test_response_contains_roadmap_key(self, mock_roadmap_cls, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = make_preference()
        mock_roadmap_cls.return_value.generate_roadmap.return_value = [
            {"phase": "Month 1", "steps": ["Step A"]}
        ]
        response = client.get("/roadmap/1")
        assert "roadmap" in response.json()

    def test_returns_404_when_no_preferences_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.get("/roadmap/99")
        assert response.status_code == 404

    def test_404_detail_mentions_preferences(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.get("/roadmap/99")
        assert "preference" in response.json()["detail"].lower()