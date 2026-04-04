"""Quick-action (no session) unit tests for `chat.services.chat_service`."""

from unittest.mock import MagicMock, patch

import pytest

from chat.services.chat_service import explain_task, get_suggested_questions, msg_to_dict

from chat.tests.service.utils.chat_service_test_utils import (
    ALT_MESSAGE_ID_5,
    DEFAULT_GOAL_ID,
    DEFAULT_TASK_ID,
    DEFAULT_USER_ID,
    OTHER_USER_ID,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    make_goal,
    make_message,
    make_task,
    set_first_result,
    set_first_side_effect,
    set_task_query_results,
)


# Explain Task


@patch(
    "chat.services.chat_service.call_chat_llm",
    return_value="This task means you need to write a compelling SOP.",
)
def test_explain_returns(mock_llm):
    db = MagicMock()
    task = make_task(goal_id=DEFAULT_GOAL_ID)
    goal = make_goal()

    set_first_side_effect(db, [task, goal])
    set_task_query_results(db, [])

    result = explain_task(db, user_id=DEFAULT_USER_ID, task_id=DEFAULT_TASK_ID)

    assert isinstance(result, str)
    assert "SOP" in result


def test_explain_missing_task():
    db = MagicMock()
    set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        explain_task(db, user_id=DEFAULT_USER_ID, task_id=999)

    assert exc_info.value.status_code == HTTP_NOT_FOUND


@patch("chat.services.chat_service.call_chat_llm")
def test_explain_other_user(mock_llm):
    db = MagicMock()
    task = make_task(goal_id=DEFAULT_GOAL_ID)

    set_first_side_effect(db, [task, None])

    with pytest.raises(Exception) as exc_info:
        explain_task(db, user_id=OTHER_USER_ID, task_id=DEFAULT_TASK_ID)

    assert exc_info.value.status_code == HTTP_FORBIDDEN


# Suggested questions


@patch(
    "chat.services.chat_service.generate_suggestions",
    return_value=["Q1", "Q2", "Q3"],
)
def test_get_suggested_returns(mock_gen):
    db = MagicMock()
    goal = make_goal(user_id=DEFAULT_USER_ID)
    set_first_result(db, goal)

    result = get_suggested_questions(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert result == ["Q1", "Q2", "Q3"]


def test_get_suggested_empty():
    db = MagicMock()
    set_first_result(db, None)

    result = get_suggested_questions(db, user_id=OTHER_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert result == []


# Helpers


def test_msg_to_dict():
    msg = make_message(id=ALT_MESSAGE_ID_5, role="assistant", content="Hello there")

    result = msg_to_dict(msg)

    assert result["id"] == ALT_MESSAGE_ID_5
    assert result["role"] == "assistant"
    assert result["content"] == "Hello there"
    assert "created_at" in result
