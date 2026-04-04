# services/chat_service.py
"""
AI Chat Service for in-app goal/task guidance.

Architecture:
- Each LLM call includes: system prompt + goal/task context + conversation history + user message
- Context is rebuilt on every call (not cached) so it always reflects the latest task state
- Conversation history is loaded from DB, trimmed to last N messages to stay within token limits
- No LangGraph needed — this is a standard context-augmented chat pattern

Token budget (rough):
  system prompt ~300 tokens
  goal/task context ~500-1500 tokens
  conversation history ~2000 tokens (last 20 messages)
  user message ~200 tokens
  ≈ 3000-4000 tokens input → well within gpt-4o-mini's 128k window
"""

import os
import json
import logging
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from chat.services import context_builder as _context_builder
from chat.services import rate_limit as _rate_limit


from goals.models.goal_models import Goal
from goals.models.task_models import Task
from chat.models.chat_models import ChatSession, ChatMessage


logger = logging.getLogger(__name__)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"

MAX_HISTORY_MESSAGES = 20
SESSION_TITLE_MAX_LENGTH = 80
CHAT_LLM_TEMPERATURE = 0.4
CHAT_LLM_MAX_TOKENS = 800
SUGGESTIONS_LLM_TEMPERATURE = 0.5
SUGGESTIONS_LLM_MAX_TOKENS = 200
MIN_SUGGESTIONS_REQUIRED = 2
MAX_SUGGESTIONS_RETURNED = 3
SSE_DATA_PREFIX_LENGTH = 6
LAST_MESSAGE_PREVIEW_LENGTH = 100


# ─── Context Building / Rate limiting moved to smaller modules ───────


# ─── Session Management ──────────────────────────────────────────────


def create_chat_session(
    db: Session,
    user_id: int,
    goal_id: int,
    task_id: int | None,
    first_message: str,
) -> dict:
    """Create a new chat session and get the first AI response."""

    # Rate limit
    if not check_rate_limit(db, user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages.",
        )

    # Validate ownership
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found or not yours")

    task = None
    if task_id:
        task = (
            db.query(Task).filter(Task.id == task_id, Task.goal_id == goal_id).first()
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found for this goal")

    # Create session
    session = ChatSession(
        user_id=user_id,
        goal_id=goal_id,
        task_id=task_id,
    )
    db.add(session)
    db.flush()

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=first_message)
    db.add(user_msg)
    db.flush()

    # Build context and get AI response
    goal_context = build_goal_context(db, goal)
    task_context = build_task_context(task) if task else ""
    system_prompt = build_system_prompt(has_task_focus=task is not None)

    full_context = goal_context
    if task_context:
        full_context += "\n" + task_context

    assistant_reply = call_chat_llm(
        system_prompt=system_prompt,
        context=full_context,
        history=[],
        user_message=first_message,
    )

    # Store assistant reply
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=assistant_reply,
    )
    db.add(assistant_msg)

    # Auto-generate session title
    title_suffix = "..." if len(first_message) > SESSION_TITLE_MAX_LENGTH else ""
    session.title = first_message[:SESSION_TITLE_MAX_LENGTH] + title_suffix
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "user_message": msg_to_dict(user_msg),
        "assistant_message": msg_to_dict(assistant_msg),
    }


def send_message(
    db: Session,
    user_id: int,
    session_id: int,
    message: str,
) -> dict:
    """Send a follow-up message in an existing chat session."""

    # Rate limit
    if not check_rate_limit(db, user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages.",
        )

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if not session.is_active:
        raise HTTPException(status_code=400, detail="This chat session is closed")

    # Load goal (and optionally task) for fresh context
    goal = db.query(Goal).filter(Goal.id == session.goal_id).first()
    task = (
        db.query(Task).filter(Task.id == session.task_id).first()
        if session.task_id
        else None
    )

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_msg)
    db.flush()

    # Build context fresh (reflects latest task statuses)
    goal_context = build_goal_context(db, goal)
    task_context = build_task_context(task) if task else ""
    system_prompt = build_system_prompt(has_task_focus=task is not None)

    full_context = goal_context
    if task_context:
        full_context += "\n" + task_context

    # Load conversation history (last N messages, excluding the one we just added)
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_messages[-MAX_HISTORY_MESSAGES - 1: -1]
    ]

    assistant_reply = call_chat_llm(
        system_prompt=system_prompt,
        context=full_context,
        history=history,
        user_message=message,
    )

    # Store assistant reply
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=assistant_reply,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "user_message": msg_to_dict(user_msg),
        "assistant_message": msg_to_dict(assistant_msg),
    }


def get_chat_history(db: Session, user_id: int, session_id: int) -> dict:
    """Get full chat history for a session."""

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )

    return {
        "session_id": session.id,
        "goal_id": session.goal_id,
        "task_id": session.task_id,
        "title": session.title,
        "messages": [msg_to_dict(m) for m in messages],
    }


def list_sessions_for_goal(db: Session, user_id: int, goal_id: int) -> list[dict]:
    """List all chat sessions for a goal."""

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id, ChatSession.goal_id == goal_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )

    result = []
    for s in sessions:
        last_msg = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.created_at.desc())
            .first()
        )
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        last_preview = (
            last_msg.content[:LAST_MESSAGE_PREVIEW_LENGTH] if last_msg else None
        )

        result.append(
            {
                "id": s.id,
                "goal_id": s.goal_id,
                "task_id": s.task_id,
                "title": s.title,
                "message_count": msg_count,
                "last_message_preview": last_preview,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
        )

    return result


# ─── Quick Actions (no session needed) ───────────────────────────────


def explain_task(db: Session, user_id: int, task_id: int) -> str:
    """
    One-shot explanation of a task — no session created.
    Good for the "Explain this" button on a task card.
    """

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    goal = (
        db.query(Goal).filter(Goal.id == task.goal_id, Goal.user_id == user_id).first()
    )
    if not goal:
        raise HTTPException(status_code=403, detail="Not your task")

    goal_context = build_goal_context(db, goal)
    task_context = build_task_context(task)

    prompt_lines = [
        "Explain this task to the user in a helpful way:",
        "",
        goal_context,
        "",
        task_context,
        "",
        "Provide:",
        "1. What this task means in plain language",
        "2. 3-5 concrete steps to complete it",
        "3. One practical tip or example",
        "",
        "Keep it under 250 words. Be specific to their goal, not generic.",
    ]
    prompt = "\n".join(prompt_lines)

    return call_chat_llm(
        system_prompt="You are a helpful productivity coach. Be concise and actionable.",
        context="",
        history=[],
        user_message=prompt,
    )


# ─── Streaming Chat ──────────────────────────────────────────────────


def _prepare_streaming_messages(
    system_prompt: str,
    full_context: str,
    history: list[dict],
    message: str,
) -> list[dict]:
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if full_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    f"Here is the user's current goal and task data:\n\n{full_context}"
                ),
            }
        )
    messages.extend(history)
    messages.append({"role": "user", "content": message})
    return messages


_STREAM_DONE_SENTINEL = "__STREAM_DONE__"


def _extract_stream_token(line: bytes) -> str | None:
    if not line:
        return None
    line_str = line.decode("utf-8")
    if not line_str.startswith("data: "):
        return None

    data_str = line_str[SSE_DATA_PREFIX_LENGTH:]
    if data_str.strip() == "[DONE]":
        return _STREAM_DONE_SENTINEL

    try:
        chunk = json.loads(data_str)
    except json.JSONDecodeError:
        logger.debug("Skipping malformed SSE chunk")
        return None

    delta = chunk.get("choices", [{}])[0].get("delta", {})
    return delta.get("content", "")


def _generate_event_stream(
    db: Session,
    session: ChatSession,
    messages: list[dict],
    goal: Goal,
    task: Task,
):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": CHAT_LLM_TEMPERATURE,
        "max_tokens": CHAT_LLM_MAX_TOKENS,
        "stream": True,
    }

    full_response = ""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60,
            stream=True,
        )
        response.raise_for_status()

        for line in response.iter_lines():
            token = _extract_stream_token(line)
            if token is None:
                continue
            if token == _STREAM_DONE_SENTINEL:
                break
            if token:
                full_response += token
                token_payload = {"token": token}
                yield f"data: {json.dumps(token_payload)}\n\n"

        # Store the full assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=full_response,
        )
        db.add(assistant_msg)
        db.commit()

        # Send done signal with suggestions
        suggestions = generate_suggestions(
            goal_title=goal.title if goal else "",
            task_title=task.title if task else "",
            last_response=full_response[:300],
        )
        suggestions_payload = {"suggestions": suggestions}
        yield f"data: {json.dumps(suggestions_payload)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        print(f"Streaming error: {e}")
        error_payload = {"token": " [Error generating response. Please try again.]"}
        yield f"data: {json.dumps(error_payload)}\n\n"
        yield "data: [DONE]\n\n"


def stream_message(
    db: Session,
    user_id: int,
    session_id: int,
    message: str,
):
    """
    Stream assistant response token-by-token via SSE.
    Returns a StreamingResponse.
    """

    # Rate limit
    if not check_rate_limit(db, user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before sending more messages.",
        )

    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    if not session.is_active:
        raise HTTPException(status_code=400, detail="This chat session is closed")

    # Load goal/task for context
    goal = db.query(Goal).filter(Goal.id == session.goal_id).first()
    task = (
        db.query(Task).filter(Task.id == session.task_id).first()
        if session.task_id
        else None
    )

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_msg)
    db.flush()

    # Build context
    goal_context = build_goal_context(db, goal)
    task_context = build_task_context(task) if task else ""
    system_prompt = build_system_prompt(has_task_focus=task is not None)
    if task_context:
        full_context = goal_context + "\n" + task_context
    else:
        full_context = goal_context

    # Load history
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_messages[-MAX_HISTORY_MESSAGES - 1: -1]
    ]

    # Build LLM messages
    messages = _prepare_streaming_messages(
        system_prompt,
        full_context,
        history,
        message,
    )

    return StreamingResponse(
        _generate_event_stream(db, session, messages, goal, task),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Suggested Questions ─────────────────────────────────────────────


def get_suggested_questions(
    db: Session,
    user_id: int,
    goal_id: int,
    task_id: int = None,
) -> list[str]:
    """
    Generate 2-3 contextual follow-up questions based on the goal/task.
    Called on initial load and after each response.
    """

    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not goal:
        return []

    task = None
    if task_id:
        task = (
            db.query(Task).filter(Task.id == task_id, Task.goal_id == goal_id).first()
        )

    goal_title = goal.title
    task_title = task.title if task else None

    return generate_suggestions(goal_title, task_title)


def _generate_suggestions(
    goal_title: str,
    task_title: str = None,
    last_response: str = None,
) -> list[str]:
    """Ask LLM for 2-3 suggested follow-up questions."""

    context = _build_suggestions_context(goal_title, task_title, last_response)
    prompt = _build_suggestions_prompt(context)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Return only a JSON array of 3 strings."},
            {"role": "user", "content": prompt},
        ],
        "temperature": SUGGESTIONS_LLM_TEMPERATURE,
        "max_tokens": SUGGESTIONS_LLM_MAX_TOKENS,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        suggestions = _parse_suggestions_response(content)
        if suggestions and len(suggestions) >= MIN_SUGGESTIONS_REQUIRED:
            return suggestions[:MAX_SUGGESTIONS_RETURNED]
    except Exception as e:
        print(f"Suggestion generation error: {e}")

    return _fallback_suggestions(task_title)


def _build_suggestions_context(
    goal_title: str,
    task_title: str | None,
    last_response: str | None,
) -> str:
    context = f"Goal: {goal_title}"
    if task_title:
        context += f"\nCurrent task: {task_title}"
    if last_response:
        context += f"\nLast AI response (excerpt): {last_response}"
    return context


def _build_suggestions_prompt(context: str) -> str:
    prompt_lines = [
        "Given this context:",
        context,
        "",
        "Generate exactly 3 short follow-up questions a user might want to ask.",
        "Each question should be specific to the goal/task, not generic.",
        "Keep each under 60 characters.",
        "",
        "Return ONLY a JSON array of 3 strings, nothing else.",
        "Example:",
        (
            '["How long does step 2 take?", "What tools do I need?", "Can I skip the review?"]'
        ),
    ]
    return "\n".join(prompt_lines)


def _parse_suggestions_response(content: str) -> list[str] | None:
    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()
    try:
        suggestions = json.loads(content)
    except json.JSONDecodeError:
        logger.debug("Could not parse suggestions response as JSON")
        return None
    return suggestions if isinstance(suggestions, list) else None


def _fallback_suggestions(task_title: str | None) -> list[str]:
    if task_title:
        return [
            "How do I complete this task?",
            "What should I do if I get stuck?",
            "What comes after this task?",
        ]
    return [
        "What should I focus on today?",
        "Am I on track with my goal?",
        "Break down my next task for me",
    ]


# ─── LLM Call ────────────────────────────────────────────────────────


def _call_chat_llm(
    system_prompt: str,
    context: str,
    history: list[dict],
    user_message: str,
) -> str:
    """
    Send a chat completion request with:
    - system prompt (role definition)
    - context injected as a system message (goal/task data)
    - conversation history (previous turns)
    - latest user message
    """

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    if context:
        messages.append(
            {
                "role": "system",
                "content": (
                    f"Here is the user's current goal and task data:\n\n{context}"
                ),
            }
        )

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": CHAT_LLM_TEMPERATURE,
        "max_tokens": CHAT_LLM_MAX_TOKENS,
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"Chat LLM error: {e}")
        return (
            "I'm having trouble generating a response right now. "
            "Please try again in a moment. If the issue persists, "
            "check your internet connection or try refreshing the page."
        )


# ─── Helpers ─────────────────────────────────────────────────────────


def _msg_to_dict(msg: ChatMessage) -> dict:
    return {
        "id": msg.id,
        "role": msg.role,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


# ─── Public wrappers (test-friendly) ────────────────────────────────


def build_goal_context(db: Session, goal: Goal) -> str:
    return _context_builder.build_goal_context(db, goal)


def build_task_context(task: Task) -> str:
    return _context_builder.build_task_context(task)


def build_system_prompt(has_task_focus: bool) -> str:
    return _context_builder.build_system_prompt(has_task_focus)


def check_rate_limit(db: Session, user_id: int) -> bool:
    return _rate_limit.check_rate_limit(db, user_id)


def call_chat_llm(
    system_prompt: str,
    context: str,
    history: list[dict],
    user_message: str,
) -> str:
    return _call_chat_llm(system_prompt, context, history, user_message)


def generate_suggestions(
    goal_title: str,
    task_title: str | None = None,
    last_response: str | None = None,
) -> list[str]:
    return _generate_suggestions(goal_title, task_title, last_response)


def msg_to_dict(msg: ChatMessage) -> dict:
    return _msg_to_dict(msg)
