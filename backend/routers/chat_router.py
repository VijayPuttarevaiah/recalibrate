# routes/chat_routes.py
"""
Chat API routes for in-app AI guidance.

Endpoints:
  POST   /chat/sessions                       — Start a new chat (about a goal or task)
  POST   /chat/sessions/{id}/messages          — Send a follow-up message (non-streaming)
  POST   /chat/sessions/{id}/messages/stream   — Send a follow-up message (SSE streaming)
  GET    /chat/sessions/{id}                   — Get full chat history
  GET    /chat/sessions?goal_id=X              — List all sessions for a goal
  POST   /chat/explain/task/{id}               — Quick one-shot task explanation (no session)
  GET    /chat/suggestions                     — Get suggested follow-up questions
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from schemas.chat_schemas import (
    ChatSessionCreate,
    ChatMessageRequest,
    ChatReplyResponse,
    ChatHistoryResponse,
    ChatSessionListItem,
)
from services.chat_service import (
    create_chat_session,
    send_message,
    stream_message,
    get_chat_history,
    list_sessions_for_goal,
    explain_task,
    get_suggested_questions,
)
from utils.db_session import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["ai-chat"])


# ── 1. Start a new chat session ──

@router.post("/sessions", response_model=ChatReplyResponse)
def start_chat_session(
    body: ChatSessionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new chat session scoped to a goal (and optionally a task).
    Sends the first message and returns the AI's response.

    Example request:
    {
        "goal_id": 5,
        "task_id": 42,          // optional — omit for goal-level chat
        "message": "What does this task mean? How should I approach it?"
    }
    """
    return create_chat_session(
        db=db,
        user_id=current_user["user_id"],
        goal_id=body.goal_id,
        task_id=body.task_id,
        first_message=body.message,
    )


# ── 2. Send a follow-up message (non-streaming) ──

@router.post("/sessions/{session_id}/messages", response_model=ChatReplyResponse)
def send_chat_message(
    session_id: int,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a follow-up message in an existing session.
    The AI remembers the full conversation context.
    Returns the complete response at once.
    """
    return send_message(
        db=db,
        user_id=current_user["user_id"],
        session_id=session_id,
        message=body.message,
    )


# ── 3. Send a follow-up message (STREAMING via SSE) ──

@router.post("/sessions/{session_id}/messages/stream")
def stream_chat_message(
    session_id: int,
    body: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stream the AI response token-by-token via Server-Sent Events.

    The frontend should read this as an SSE stream:
    - Each event: data: {"token": "word"}
    - Final event before [DONE]: data: {"suggestions": ["q1", "q2", "q3"]}
    - End signal: data: [DONE]
    """
    return stream_message(
        db=db,
        user_id=current_user["user_id"],
        session_id=session_id,
        message=body.message,
    )


# ── 4. Get full chat history ──

@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
def get_session_history(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the complete message history for a chat session."""
    user_id = current_user["user_id"]
    return get_chat_history(db, user_id, session_id)


# ── 5. List sessions for a goal ──

@router.get("/sessions", response_model=list[ChatSessionListItem])
def list_chat_sessions(
    goal_id: int = Query(..., description="Filter sessions by goal"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all chat sessions for a specific goal (most recent first)."""
    user_id = current_user["user_id"]
    return list_sessions_for_goal(db, user_id, goal_id)


# ── 6. Quick one-shot task explanation ──

@router.post("/explain/task/{task_id}")
def explain_task_endpoint(
    task_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Quick "Explain this" button — no session created.
    Returns a one-shot explanation of the task.

    If the user wants to ask follow-up questions,
    they should start a full session via POST /chat/sessions.
    """
    user_id = current_user["user_id"]
    explanation = explain_task(db, user_id, task_id)
    return {"task_id": task_id, "explanation": explanation}


# ── 7. Get suggested questions ──

@router.get("/suggestions")
def get_suggestions(
    goal_id: int = Query(...),
    task_id: int = Query(default=None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get 2-3 suggested follow-up questions for a goal/task.
    Called on chat open and after each AI response.
    """
    suggestions = get_suggested_questions(
        db=db,
        user_id=current_user["user_id"],
        goal_id=goal_id,
        task_id=task_id,
    )
    return {"suggestions": suggestions}