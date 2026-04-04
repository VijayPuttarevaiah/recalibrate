"""Rate-limiting helpers for chat.

Separated from `chat_service.py` to keep orchestration code small and readable.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from chat.models.chat_models import ChatMessage, ChatSession

RATE_LIMIT_PER_HOUR = 50


def check_rate_limit(db: Session, user_id: int) -> bool:
    """Return True if the user is allowed to send another message."""

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
