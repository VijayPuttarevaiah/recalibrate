# backend/tests/routers/test_chat_router.py
"""
RED: Unit tests for chat API endpoints.
Service layer is fully mocked — tests only verify HTTP behavior:
status codes, response shapes, validation errors.
"""

import pytest
from unittest.mock import patch, MagicMock


# ═══════════════════════════════════════════════════════
# POST /chat/sessions
# ═══════════════════════════════════════════════════════

class TestStartSession:

    @patch("routers.chat_router.create_chat_session")
    def test_200_on_success(self, mock_create, auth_client):
        mock_create.return_value = {
            "session_id": 1,
            "user_message": {"id": 1, "role": "user", "content": "Hi", "created_at": "2026-03-18T10:00:00"},
            "assistant_message": {"id": 2, "role": "assistant", "content": "Hello!", "created_at": "2026-03-18T10:00:01"},
        }

        res = auth_client.post("/chat/sessions", json={"goal_id": 5, "message": "Hi"})

        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == 1
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"

    @patch("routers.chat_router.create_chat_session")
    def test_200_with_task_id(self, mock_create, auth_client):
        mock_create.return_value = {
            "session_id": 1,
            "user_message": {"id": 1, "role": "user", "content": "Explain", "created_at": ""},
            "assistant_message": {"id": 2, "role": "assistant", "content": "Sure", "created_at": ""},
        }

        res = auth_client.post("/chat/sessions", json={"goal_id": 5, "task_id": 42, "message": "Explain"})
        assert res.status_code == 200

    def test_422_missing_message(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"goal_id": 5})
        assert res.status_code == 422

    def test_422_empty_message(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"goal_id": 5, "message": ""})
        assert res.status_code == 422

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.post("/chat/sessions", json={"message": "Hello"})
        assert res.status_code == 422


# ═══════════════════════════════════════════════════════
# POST /chat/sessions/{id}/messages
# ═══════════════════════════════════════════════════════

class TestSendMessage:

    @patch("routers.chat_router.send_message")
    def test_200_follow_up(self, mock_send, auth_client):
        mock_send.return_value = {
            "session_id": 1,
            "user_message": {"id": 3, "role": "user", "content": "More?", "created_at": ""},
            "assistant_message": {"id": 4, "role": "assistant", "content": "Sure!", "created_at": ""},
        }

        res = auth_client.post("/chat/sessions/1/messages", json={"message": "More?"})

        assert res.status_code == 200
        assert res.json()["session_id"] == 1

    def test_422_empty_message(self, auth_client):
        res = auth_client.post("/chat/sessions/1/messages", json={"message": ""})
        assert res.status_code == 422


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

        res = auth_client.post("/chat/sessions/1/messages/stream", json={"message": "Test"})

        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")


# ═══════════════════════════════════════════════════════
# GET /chat/sessions/{id}
# ═══════════════════════════════════════════════════════

class TestGetHistory:

    @patch("routers.chat_router.get_chat_history")
    def test_200_returns_messages(self, mock_history, auth_client):
        mock_history.return_value = {
            "session_id": 1,
            "goal_id": 5,
            "task_id": None,
            "title": "My chat",
            "messages": [
                {"id": 1, "role": "user", "content": "Hi", "created_at": ""},
                {"id": 2, "role": "assistant", "content": "Hello!", "created_at": ""},
            ],
        }

        res = auth_client.get("/chat/sessions/1")

        assert res.status_code == 200
        data = res.json()
        assert data["session_id"] == 1
        assert len(data["messages"]) == 2


# ═══════════════════════════════════════════════════════
# GET /chat/sessions?goal_id=X
# ═══════════════════════════════════════════════════════

class TestListSessions:

    @patch("routers.chat_router.list_sessions_for_goal")
    def test_200_returns_list(self, mock_list, auth_client):
        mock_list.return_value = [{
            "id": 1, "goal_id": 5, "task_id": None, "title": "Chat",
            "message_count": 2, "last_message_preview": "Hello",
            "created_at": "2026-03-18T10:00:00", "updated_at": "2026-03-18T10:05:00",
        }]

        res = auth_client.get("/chat/sessions?goal_id=5")

        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.get("/chat/sessions")
        assert res.status_code == 422


# ═══════════════════════════════════════════════════════
# POST /chat/explain/task/{id}
# ═══════════════════════════════════════════════════════

class TestExplainTask:

    @patch("routers.chat_router.explain_task")
    def test_200_returns_explanation(self, mock_explain, auth_client):
        mock_explain.return_value = "This task means you should write an SOP."

        res = auth_client.post("/chat/explain/task/42")

        assert res.status_code == 200
        data = res.json()
        assert data["task_id"] == 42
        assert "explanation" in data


# ═══════════════════════════════════════════════════════
# GET /chat/suggestions
# ═══════════════════════════════════════════════════════

class TestSuggestions:

    @patch("routers.chat_router.get_suggested_questions")
    def test_200_returns_suggestions(self, mock_suggest, auth_client):
        mock_suggest.return_value = ["Q1?", "Q2?", "Q3?"]

        res = auth_client.get("/chat/suggestions?goal_id=5")

        assert res.status_code == 200
        assert len(res.json()["suggestions"]) == 3

    @patch("routers.chat_router.get_suggested_questions")
    def test_with_task_id(self, mock_suggest, auth_client):
        mock_suggest.return_value = ["Q1?", "Q2?", "Q3?"]

        res = auth_client.get("/chat/suggestions?goal_id=5&task_id=42")
        assert res.status_code == 200

    def test_422_missing_goal_id(self, auth_client):
        res = auth_client.get("/chat/suggestions")
        assert res.status_code == 422