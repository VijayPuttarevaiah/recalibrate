# backend/tests/models/test_chat_models.py
"""
Unit tests for ChatSession and ChatMessage models.
Pure structure tests — no database needed.
"""

from sqlalchemy import inspect
from chat.models.chat_models import ChatMessage, ChatSession

def test_session_tablename():
    mapper = inspect(ChatSession)
    assert mapper.local_table.name == "chat_sessions"

def test_session_columns():
    columns = [c.name for c in inspect(ChatSession).local_table.columns]
    assert "id" in columns
    assert "user_id" in columns
    assert "goal_id" in columns
    assert "task_id" in columns
    assert "title" in columns
    assert "is_active" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

def test_session_user_required():
    col = inspect(ChatSession).local_table.columns["user_id"]
    assert col.nullable is False

def test_session_goal_required():
    col = inspect(ChatSession).local_table.columns["goal_id"]
    assert col.nullable is False

def test_session_task_optional():
    col = inspect(ChatSession).local_table.columns["task_id"]
    assert col.nullable is True

def test_session_title_nullable():
    col = inspect(ChatSession).local_table.columns["title"]
    assert col.nullable is True

def test_session_goal_fk():
    col = inspect(ChatSession).local_table.columns["goal_id"]
    fk = list(col.foreign_keys)
    assert len(fk) == 1
    assert "goals.id" in str(fk[0])

def test_session_user_fk():
    col = inspect(ChatSession).local_table.columns["user_id"]
    fk = list(col.foreign_keys)
    assert len(fk) == 1
    assert "users.id" in str(fk[0])

def test_session_task_fk():
    col = inspect(ChatSession).local_table.columns["task_id"]
    fk = list(col.foreign_keys)
    assert len(fk) == 1
    assert "tasks.id" in str(fk[0])

def test_session_goal_rel():
    rels = [r.key for r in inspect(ChatSession).relationships]
    assert "goal" in rels

def test_session_task_rel():
    rels = [r.key for r in inspect(ChatSession).relationships]
    assert "task" in rels

def test_session_messages_rel():
    rels = [r.key for r in inspect(ChatSession).relationships]
    assert "messages" in rels

def test_message_tablename():
    mapper = inspect(ChatMessage)
    assert mapper.local_table.name == "chat_messages"

def test_message_columns():
    columns = [c.name for c in inspect(ChatMessage).local_table.columns]
    assert "id" in columns
    assert "session_id" in columns
    assert "role" in columns
    assert "content" in columns
    assert "created_at" in columns

def test_message_session_required():
    col = inspect(ChatMessage).local_table.columns["session_id"]
    assert col.nullable is False

def test_message_role_required():
    col = inspect(ChatMessage).local_table.columns["role"]
    assert col.nullable is False

def test_message_content_required():
    col = inspect(ChatMessage).local_table.columns["content"]
    assert col.nullable is False

def test_message_session_fk():
    col = inspect(ChatMessage).local_table.columns["session_id"]
    fk = list(col.foreign_keys)
    assert len(fk) == 1
    assert "chat_sessions.id" in str(fk[0])

def test_message_session_rel():
    rels = [r.key for r in inspect(ChatMessage).relationships]
    assert "session" in rels
