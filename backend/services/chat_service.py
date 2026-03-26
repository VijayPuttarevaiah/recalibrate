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
import requests
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from models.goal_models import Goal
from models.task_models import Task
from models.chat_models import ChatSession, ChatMessage


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "openai/gpt-4o-mini"

MAX_HISTORY_MESSAGES = 20
RATE_LIMIT_PER_HOUR = 50


# ─── Context Building ────────────────────────────────────────────────

def _build_goal_context(db: Session, goal: Goal) -> str:
    """Build a rich context string from goal + its tasks."""

    tasks = (
        db.query(Task)
        .filter(Task.goal_id == goal.id)
        .order_by(Task.due_date)
        .all()
    )

    today = date.today()

    completed = [t for t in tasks if t.status == "completed"]
    pending = [t for t in tasks if t.status == "pending"]
    missed = [t for t in tasks if t.status == "missed"]
    overdue = [t for t in tasks if t.status == "pending" and t.due_date < today]

    today_tasks = [t for t in tasks if t.due_date == today]
    upcoming = [t for t in pending if t.due_date > today][:7]

    context = f"""=== GOAL CONTEXT ===
Title: {goal.title}
Category: {goal.category}
Timeline: {goal.start_date} → {goal.end_date}
Status: {goal.status}
Notes: {goal.notes or "None"}

=== PROGRESS ===
Total tasks: {len(tasks)}
Completed: {len(completed)}
Pending: {len(pending)}
Missed: {len(missed)}
Overdue: {len(overdue)}
Days remaining: {(goal.end_date - today).days}

=== RECENTLY COMPLETED (last 5) ===
"""
    for t in completed[-5:]:
        notes_snippet = f" | Notes: {t.notes[:100]}" if t.notes else ""
        context += f"- [{t.due_date}] {t.title}{notes_snippet}\n"

    context += "\n=== TODAY'S TASKS ===\n"
    if today_tasks:
        for t in today_tasks:
            context += f"- {t.title} (status: {t.status})\n"
    else:
        context += "- No tasks scheduled for today\n"

    context += "\n=== UPCOMING (next 7 days) ===\n"
    for t in upcoming:
        context += f"- [{t.due_date}] {t.title}\n"

    if overdue:
        context += "\n=== OVERDUE TASKS ===\n"
        for t in overdue[:5]:
            context += f"- [{t.due_date}] {t.title}\n"

    return context


def _build_task_context(task: Task) -> str:
    """Build focused context for a specific task."""

    context = f"""=== FOCUSED TASK ===
Title: {task.title}
Due Date: {task.due_date}
Status: {task.status}
Description: {task.description or "No description"}
User Notes: {task.notes or "No notes yet"}
"""
    return context


def _build_system_prompt(has_task_focus: bool) -> str:
    """System prompt for the chat assistant."""

    base = """You are an AI productivity coach embedded in a goal-tracking app. \
Your job is to help users understand and execute their goals and tasks.

Your capabilities:
1. EXPLAIN what a goal or task means in practical terms
2. BREAK DOWN complex tasks into clear, actionable steps
3. PROVIDE examples, best practices, and tips relevant to the task
4. ANSWER follow-up questions conversationally
5. MOTIVATE the user based on their actual progress

Rules:
- Be concise but thorough. Prefer short paragraphs over long walls of text.
- Be specific to the user's actual goal and tasks — don't give generic advice.
- Reference their progress data (completed tasks, missed tasks) when relevant.
- If a task seems unclear, explain what it likely means AND suggest how to approach it.
- If the user is behind schedule, be encouraging but honest about what needs to happen.
- Use the task notes (if any) to understand what the user has already tried.
- Format steps as numbered lists when breaking things down.
- Keep responses under 400 words unless the user asks for more detail.
"""

    if has_task_focus:
        base += """
You are currently focused on a SPECIFIC TASK. Prioritize explaining that task, \
but you can reference the broader goal context when helpful.
"""

    return base


# ─── Rate Limiting ───────────────────────────────────────────────────

def _check_rate_limit(db: Session, user_id: int) -> bool:
    """Check if user has exceeded message rate limit (50/hour)."""
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    count = (
        db.query(func.count(ChatMessage.id))
        .join(ChatSession)
        .filter(
            ChatSession.user_id == user_id,
            ChatMessage.role == "user",
            ChatMessage.created_at >= one_hour_ago,
        )
        .scalar()
    )
    return count < RATE_LIMIT_PER_HOUR


# ─── Session Management ──────────────────────────────────────────────

def create_chat_session(
    db: Session, user_id: int, goal_id: int, task_id: int | None, first_message: str
) -> dict:
    """Create a new chat session and get the first AI response."""

    # Rate limit
    if not _check_rate_limit(db, user_id):
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
        task = db.query(Task).filter(Task.id == task_id, Task.goal_id == goal_id).first()
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
    goal_context = _build_goal_context(db, goal)
    task_context = _build_task_context(task) if task else ""
    system_prompt = _build_system_prompt(has_task_focus=task is not None)

    full_context = goal_context
    if task_context:
        full_context += "\n" + task_context

    assistant_reply = _call_chat_llm(
        system_prompt=system_prompt,
        context=full_context,
        history=[],
        user_message=first_message,
    )

    # Store assistant reply
    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=assistant_reply)
    db.add(assistant_msg)

    # Auto-generate session title
    session.title = first_message[:80] + ("..." if len(first_message) > 80 else "")
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "user_message": _msg_to_dict(user_msg),
        "assistant_message": _msg_to_dict(assistant_msg),
    }


def send_message(db: Session, user_id: int, session_id: int, message: str) -> dict:
    """Send a follow-up message in an existing chat session."""

    # Rate limit
    if not _check_rate_limit(db, user_id):
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
    task = db.query(Task).filter(Task.id == session.task_id).first() if session.task_id else None

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_msg)
    db.flush()

    # Build context fresh (reflects latest task statuses)
    goal_context = _build_goal_context(db, goal)
    task_context = _build_task_context(task) if task else ""
    system_prompt = _build_system_prompt(has_task_focus=task is not None)

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
        for m in history_messages[-MAX_HISTORY_MESSAGES - 1:-1]
    ]

    assistant_reply = _call_chat_llm(
        system_prompt=system_prompt,
        context=full_context,
        history=history,
        user_message=message,
    )

    # Store assistant reply
    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=assistant_reply)
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "user_message": _msg_to_dict(user_msg),
        "assistant_message": _msg_to_dict(assistant_msg),
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
        "messages": [_msg_to_dict(m) for m in messages],
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

        result.append({
            "id": s.id,
            "goal_id": s.goal_id,
            "task_id": s.task_id,
            "title": s.title,
            "message_count": msg_count,
            "last_message_preview": last_msg.content[:100] if last_msg else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        })

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

    goal = db.query(Goal).filter(Goal.id == task.goal_id, Goal.user_id == user_id).first()
    if not goal:
        raise HTTPException(status_code=403, detail="Not your task")

    goal_context = _build_goal_context(db, goal)
    task_context = _build_task_context(task)

    prompt = f"""Explain this task to the user in a helpful way:

{goal_context}

{task_context}

Provide:
1. What this task means in plain language
2. 3-5 concrete steps to complete it
3. One practical tip or example

Keep it under 250 words. Be specific to their goal, not generic."""

    return _call_chat_llm(
        system_prompt="You are a helpful productivity coach. Be concise and actionable.",
        context="",
        history=[],
        user_message=prompt,
    )


# ─── Streaming Chat ──────────────────────────────────────────────────

def stream_message(db: Session, user_id: int, session_id: int, message: str):
    """
    Stream assistant response token-by-token via SSE.
    Returns a StreamingResponse.
    """

    # Rate limit
    if not _check_rate_limit(db, user_id):
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
    task = db.query(Task).filter(Task.id == session.task_id).first() if session.task_id else None

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=message)
    db.add(user_msg)
    db.flush()

    # Build context
    goal_context = _build_goal_context(db, goal)
    task_context = _build_task_context(task) if task else ""
    system_prompt = _build_system_prompt(has_task_focus=task is not None)
    full_context = goal_context + ("\n" + task_context if task_context else "")

    # Load history
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_messages[-MAX_HISTORY_MESSAGES - 1:-1]
    ]

    # Build LLM messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    if full_context:
        messages.append({
            "role": "system",
            "content": f"Here is the user's current goal and task data:\n\n{full_context}",
        })
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    def event_stream():
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 800,
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
                if not line:
                    continue
                line_str = line.decode("utf-8")
                if not line_str.startswith("data: "):
                    continue

                data_str = line_str[6:]
                if data_str.strip() == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        full_response += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
                except json.JSONDecodeError:
                    continue

            # Store the full assistant message
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            db.commit()

            # Send done signal with suggestions
            suggestions = _generate_suggestions(
                goal_title=goal.title if goal else "",
                task_title=task.title if task else "",
                last_response=full_response[:300],
            )
            yield f"data: {json.dumps({'suggestions': suggestions})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            print(f"Streaming error: {e}")
            yield f"data: {json.dumps({'token': ' [Error generating response. Please try again.]'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Suggested Questions ─────────────────────────────────────────────

def get_suggested_questions(
    db: Session, user_id: int, goal_id: int, task_id: int = None,
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
        task = db.query(Task).filter(Task.id == task_id, Task.goal_id == goal_id).first()

    goal_title = goal.title
    task_title = task.title if task else None

    return _generate_suggestions(goal_title, task_title)


def _generate_suggestions(
    goal_title: str, task_title: str = None, last_response: str = None,
) -> list[str]:
    """Ask LLM for 2-3 suggested follow-up questions."""

    context = f"Goal: {goal_title}"
    if task_title:
        context += f"\nCurrent task: {task_title}"
    if last_response:
        context += f"\nLast AI response (excerpt): {last_response}"

    prompt = f"""Given this context:
{context}

Generate exactly 3 short follow-up questions a user might want to ask.
Each question should be specific to the goal/task, not generic.
Keep each under 60 characters.

Return ONLY a JSON array of 3 strings, nothing else.
Example: ["How long does step 2 take?", "What tools do I need?", "Can I skip the review?"]
"""

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
        "temperature": 0.5,
        "max_tokens": 200,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        suggestions = json.loads(content)
        if isinstance(suggestions, list) and len(suggestions) >= 2:
            return suggestions[:3]
    except Exception as e:
        print(f"Suggestion generation error: {e}")

    # Fallback suggestions
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
        messages.append({
            "role": "system",
            "content": f"Here is the user's current goal and task data:\n\n{context}",
        })

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 800,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30,
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