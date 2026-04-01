# backend/tests/routers/test_chat_router.py
"""
RED: Unit tests for chat API endpoints.
Service layer is fully mocked — tests only verify HTTP behavior:
status codes, response shapes, validation errors.
"""

import pytest
from unittest.mock import patch, MagicMock

HTTP_OK = 200
HTTP_UNPROCESSABLE = 422

GOAL_ID = 5
TASK_ID = 42
SESSION_ID = 1
USER_MSG_ID = 1
ASSISTANT_MSG_ID = 2
FOLLOWUP_USER_MSG_ID = 3
FOLLOWUP_ASSISTANT_MSG_ID = 4
EXPECTED_MESSAGE_COUNT = 2
EXPECTED_SUGGESTIONS_COUNT = 3
EXPECTED_LIST_COUNT = 1


# ═══════════════════════════════════════════════════════
# POST /chat/sessions
# ═══════════════════════════════════════════════════════

class TestStartSession:

    @patch("routers.chat_router.create_chat_session")
    def test_200_on_success(self, mock_create, auth_client):
        mock_create.return_value = {
            "session_id": SESSION_ID,
            "user_message": {"id": USER_MSG_ID, "role": "user", "content": "Hi", "created_at": "2026-03-18T10:00:00"},
            "assistant_message": {"id": ASSISTANT_MSG_ID, "role": "assistant", "content": "Hello!", "created_at": "2026-03-18T10:00:01"},
        }

        res = auth_client.post("/chat/sessions", json={"goal_id": GOAL_ID, "message": "Hi"})

        assert res.status_code == HTTP_OK
        data = res.json()
        assert data["session_id"] == SESSION_ID
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"

    @patch("routers.chat_router.create_chat_session")
    def test_200_with_task_id(self, mock_create, auth_client):
        mock_create.return_value = {
            "session_id": SESSION_ID,
            "user_message": {"id": USER_MSG_ID, "role": "user", "content": "Explain", "created_at": ""},
            "assistant_message": {"id": ASSISTANT_MSG_ID, "role": "assistant", "content": "Sure", "created_at": ""},
        }

        res = auth_client.post("/chat/sessions", json={"goal_id": GOAL_ID, "task_id": TASK_ID, "message": "Explain"})
        assert res.status_code == HTTP_OK

    def test_422_missing_message(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"goal_id": GOAL_ID})
        assert res.status_code == HTTP_UNPROCESSABLE

    def test_422_empty_message(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"goal_id": GOAL_ID, "message": ""})
        assert res.status_code == HTTP_UNPROCESSABLE

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"message": "Hello"})
        assert res.status_code == HTTP_UNPROCESSABLE


# ═══════════════════════════════════════════════════════
# POST /chat/sessions/{id}/messages
# ═══════════════════════════════════════════════════════

class TestSendMessage:

    @patch("routers.chat_router.send_message")
    def test_200_follow_up(self, mock_send, auth_client):
        mock_send.return_value = {
            "session_id": SESSION_ID,
            "user_message": {"id": FOLLOWUP_USER_MSG_ID, "role": "user", "content": "More?", "created_at": ""},
            "assistant_message": {"id": FOLLOWUP_ASSISTANT_MSG_ID, "role": "assistant", "content": "Sure!", "created_at": ""},
        }

        res = auth_client.post(f"/chat/sessions/{SESSION_ID}/messages", json={"message": "More?"})

        assert res.status_code == HTTP_OK
        assert res.json()["session_id"] == SESSION_ID

    def test_422_empty_message(self, auth_client):
        res = auth_client.post(f"/chat/sessions/{SESSION_ID}/messages", json={"message": ""})
        assert res.status_code == HTTP_UNPROCESSABLE


# ═══════════════════════════════════════════════════════
# POST /chat/sessions/{id}/messages/stream
# ═══════════════════════════════════════════════════════

class TestStreamMessage:

    @patch("routers.chat_router.stream_message")
    def test_returns_sse(self, mock_stream, auth_client):
        from fastapi.responses import StreamingResponse

        def fake_stream():
            yield 'data: {"token": "Hi"}\n\n'
            yield "data: [DONE]\n\n"

        mock_stream.return_value = StreamingResponse(
            fake_stream(), media_type="text/event-stream",
        )

        res = auth_client.post(f"/chat/sessions/{SESSION_ID}/messages/stream", json={"message": "Test"})

        assert res.status_code == HTTP_OK
        assert "text/event-stream" in res.headers.get("content-type", "")


# ═══════════════════════════════════════════════════════
# GET /chat/sessions/{id}
# ═══════════════════════════════════════════════════════

class TestGetHistory:

    @patch("routers.chat_router.get_chat_history")
    def test_200_returns_messages(self, mock_history, auth_client):
        mock_history.return_value = {
            "session_id": SESSION_ID,
            "goal_id": GOAL_ID,
            "task_id": None,
            "title": "My chat",
            "messages": [
                {"id": USER_MSG_ID, "role": "user", "content": "Hi", "created_at": ""},
                {"id": ASSISTANT_MSG_ID, "role": "assistant", "content": "Hello!", "created_at": ""},
            ],
        }

        res = auth_client.get(f"/chat/sessions/{SESSION_ID}")

        assert res.status_code == HTTP_OK
        data = res.json()
        assert data["session_id"] == SESSION_ID
        assert len(data["messages"]) == EXPECTED_MESSAGE_COUNT


# ═══════════════════════════════════════════════════════
# GET /chat/sessions?goal_id=X
# ═══════════════════════════════════════════════════════

class TestListSessions:

    @patch("routers.chat_router.list_sessions_for_goal")
    def test_200_returns_list(self, mock_list, auth_client):
        mock_list.return_value = [{
            "id": SESSION_ID, "goal_id": GOAL_ID, "task_id": None, "title": "Chat",
            "message_count": EXPECTED_MESSAGE_COUNT, "last_message_preview": "Hello",
            "created_at": "2026-03-18T10:00:00", "updated_at": "2026-03-18T10:05:00",
        }]

        res = auth_client.get(f"/chat/sessions?goal_id={GOAL_ID}")

        assert res.status_code == HTTP_OK
        assert len(res.json()) == EXPECTED_LIST_COUNT

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.get("/chat/sessions")
        assert res.status_code == HTTP_UNPROCESSABLE


# ═══════════════════════════════════════════════════════
# POST /chat/explain/task/{id}
# ═══════════════════════════════════════════════════════

class TestExplainTask:

    @patch("routers.chat_router.explain_task")
    def test_200_returns_explanation(self, mock_explain, auth_client):
        mock_explain.return_value = "This task means you should write an SOP."

        res = auth_client.post(f"/chat/explain/task/{TASK_ID}")

        assert res.status_code == HTTP_OK
        data = res.json()
        assert data["task_id"] == TASK_ID
        assert "explanation" in data


# ═══════════════════════════════════════════════════════
# GET /chat/suggestions
# ═══════════════════════════════════════════════════════

class TestSuggestions:

    @patch("routers.chat_router.get_suggested_questions")
    def test_200_returns_suggestions(self, mock_suggest, auth_client):
        mock_suggest.return_value = ["Q1?", "Q2?", "Q3?"]

        res = auth_client.get(f"/chat/suggestions?goal_id={GOAL_ID}")

        assert res.status_code == HTTP_OK
        assert len(res.json()["suggestions"]) == EXPECTED_SUGGESTIONS_COUNT

    @patch("routers.chat_router.get_suggested_questions")
    def test_with_task_id(self, mock_suggest, auth_client):
        mock_suggest.return_value = ["Q1?", "Q2?", "Q3?"]

        res = auth_client.get(f"/chat/suggestions?goal_id={GOAL_ID}&task_id={TASK_ID}")
        assert res.status_code == HTTP_OK

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.get("/chat/suggestions")
        assert res.status_code == HTTP_UNPROCESSABLE