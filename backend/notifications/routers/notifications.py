from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from notifications.models.notification import Notification
from notifications.services.reminder_service import check_upcoming_deadlines
from core.db_session import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _notifications_query(db: Session, user_id: int, goal_id: int | None):
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if goal_id is not None:
        q = q.filter(Notification.goal_id == goal_id)
    return q


@router.get("/{user_id}")
def get_user_notifications(
    user_id: int,
    goal_id: int | None = Query(default=None),   # ← ADD
    db: Session = Depends(get_db)
):
    notifications = (
        _notifications_query(db, user_id, goal_id)
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


@router.post("/trigger-check")
def trigger_notification_check():
    """
    Manually trigger the cron job that checks for upcoming, overdue,
    and completed tasks. Useful for demos and testing without waiting
    for the scheduled interval.
    """
    try:
        check_upcoming_deadlines()
        return {
            "success": True,
            "message": "Notification check triggered successfully",
            "data": None,
        }
    except Exception as exc:
        detail = f"Notification check failed: {str(exc)}"
        raise HTTPException(status_code=500, detail=detail)