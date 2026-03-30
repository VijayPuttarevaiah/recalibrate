from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from models.notification import Notification
from utils.db_session import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/{user_id}")
def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    """Return all notifications for a user, newest first."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return {
        "success": True,
        "message": "Notifications retrieved",
        "data": jsonable_encoder(notifications),
    }


@router.patch("/{notification_id}/read")
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a single notification as read."""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"success": True, "message": "Marked as read", "data": None}