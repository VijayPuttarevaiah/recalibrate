# backend/tests/models/test_chat_models.py
"""
RED: Unit tests for ChatSession and ChatMessage models.
Pure structure tests — no database needed.
"""

import pytest
from models.chat_models import ChatSession, ChatMessage


class TestChatSessionModel:

    def test_tablename(self):
        assert ChatSession.__tablename__ == "chat_sessions"

    def test_has_required_columns(self):
        columns = [c.name for c in ChatSession.__table__.columns]
        assert "id" in columns
        assert "user_id" in columns
        assert "goal_id" in columns
        assert "task_id" in columns
        assert "title" in columns
        assert "is_active" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_user_id_not_nullable(self):
        col = ChatSession.__table__.columns["user_id"]
        assert col.nullable is False

    def test_goal_id_not_nullable(self):
        col = ChatSession.__table__.columns["goal_id"]
        assert col.nullable is False

    def test_task_id_is_nullable(self):
        col = ChatSession.__table__.columns["task_id"]
        assert col.nullable is True

    def test_title_is_nullable(self):
        col = ChatSession.__table__.columns["title"]
        assert col.nullable is True

    def test_goal_foreign_key(self):
        col = ChatSession.__table__.columns["goal_id"]
        fk = list(col.foreign_keys)
        assert len(fk) == 1
        assert "goals.id" in str(fk[0])

    def test_user_foreign_key(self):
        col = ChatSession.__table__.columns["user_id"]
        fk = list(col.foreign_keys)
        assert len(fk) == 1
        assert "users.id" in str(fk[0])

    def test_task_foreign_key(self):
        col = ChatSession.__table__.columns["task_id"]
        fk = list(col.foreign_keys)
        assert len(fk) == 1
        assert "tasks.id" in str(fk[0])

    def test_has_goal_relationship(self):
        rels = [r.key for r in ChatSession.__mapper__.relationships]
        assert "goal" in rels

    def test_has_task_relationship(self):
        rels = [r.key for r in ChatSession.__mapper__.relationships]
        assert "task" in rels

    def test_has_messages_relationship(self):
        rels = [r.key for r in ChatSession.__mapper__.relationships]
        assert "messages" in rels


class TestChatMessageModel:

    def test_tablename(self):
        assert ChatMessage.__tablename__ == "chat_messages"

    def test_has_required_columns(self):
        columns = [c.name for c in ChatMessage.__table__.columns]
        assert "id" in columns
        assert "session_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "created_at" in columns

    def test_session_id_not_nullable(self):
        col = ChatMessage.__table__.columns["session_id"]
        assert col.nullable is False

    def test_role_not_nullable(self):
        col = ChatMessage.__table__.columns["role"]
        assert col.nullable is False

    def test_content_not_nullable(self):
        col = ChatMessage.__table__.columns["content"]
        assert col.nullable is False

    def test_session_foreign_key(self):
        col = ChatMessage.__table__.columns["session_id"]
        fk = list(col.foreign_keys)
        assert len(fk) == 1
        assert "chat_sessions.id" in str(fk[0])

    def test_has_session_relationship(self):
        rels = [r.key for r in ChatMessage.__mapper__.relationships]
        assert "session" in rels