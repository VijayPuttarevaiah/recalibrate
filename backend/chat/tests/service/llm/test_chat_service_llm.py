"""LLM-call + suggestion-generation unit tests for `chat.services.chat_service`."""

from unittest.mock import MagicMock, patch

from chat.services.chat_service import call_chat_llm, generate_suggestions

from chat.tests.service.utils.chat_service_test_utils import (
    HISTORY_ASSISTANT_COUNT,
    HISTORY_USER_COUNT,
    MESSAGES_WITHOUT_CONTEXT_COUNT,
    SUGGESTION_COUNT,
    get_post_payload,
)


@patch("chat.services.chat_service.requests.post")
def test_llm_returns_content(mock_post):
    response_payload = {"choices": [{"message": {"content": "Here is my answer."}}]}
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    result = call_chat_llm("system", "context", [], "Hello")
    assert result == "Here is my answer."


@patch("chat.services.chat_service.requests.post")
def test_llm_returns_fallback(mock_post):
    mock_post.side_effect = Exception("Connection error")

    result = call_chat_llm("system", "context", [], "Hello")
    assert "trouble generating" in result.lower()


@patch("chat.services.chat_service.requests.post")
def test_llm_sends_context(mock_post):
    response_payload = {"choices": [{"message": {"content": "OK"}}]}
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    call_chat_llm("Be helpful", "Goal: test", [], "Hi")

    payload = get_post_payload(mock_post)
    messages = payload["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "Be helpful"
    assert messages[1]["role"] == "system"
    assert "Goal: test" in messages[1]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Hi"


@patch("chat.services.chat_service.requests.post")
def test_llm_includes_history(mock_post):
    response_payload = {"choices": [{"message": {"content": "OK"}}]}
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    history = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]
    call_chat_llm("sys", "ctx", history, "Q2")

    payload = get_post_payload(mock_post)
    messages = payload["messages"]
    roles = [m["role"] for m in messages]
    assert roles.count("user") == HISTORY_USER_COUNT  # history Q1 + new Q2
    assert roles.count("assistant") == HISTORY_ASSISTANT_COUNT  # history A1


@patch("chat.services.chat_service.requests.post")
def test_llm_skips_empty_ctx(mock_post):
    response_payload = {"choices": [{"message": {"content": "OK"}}]}
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    call_chat_llm("sys", "", [], "Hi")

    payload = get_post_payload(mock_post)
    messages = payload["messages"]
    assert len(messages) == MESSAGES_WITHOUT_CONTEXT_COUNT  # system + user, no context


# Suggestions


@patch("chat.services.chat_service.requests.post")
def test_suggestions_returns3(mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": '["Q1?", "Q2?", "Q3?"]'}}]},
    )

    result = generate_suggestions("Dalhousie MACS", "Write SOP")

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT


@patch("chat.services.chat_service.requests.post")
def test_suggestions_fallback(mock_post):
    mock_post.side_effect = Exception("API down")

    result = generate_suggestions("Goal", "Task")

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT


@patch("chat.services.chat_service.requests.post")
def test_suggestions_no_task(mock_post):
    mock_post.side_effect = Exception("API down")

    result = generate_suggestions("Goal", None)

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT
    assert any("focus" in s.lower() or "track" in s.lower() for s in result)
