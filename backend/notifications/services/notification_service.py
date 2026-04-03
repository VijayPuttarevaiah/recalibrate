import logging
from sqlalchemy.orm import Session
from dataclasses import dataclass

from notifications.models.notification import Notification
from auth.utils.email_sender import send_email

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
ROADMAP_URL = "http://localhost/dashboard"


@dataclass
class NotificationParams:
    user_id: int
    title: str
    message: str
    goal_id: int | None = None
    send_mail: bool = False
    email: str | None = None


def build_email_html(title: str, message: str) -> str:
    """Build the styled HTML body for a notification email."""
    lines = [
        "<html>",
        (
            "  <body style=\"font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;"
        ),
        (
            '               line-height: 1.6; color: #1a1a1a; background-color: #f9fafb; padding: 20px;">'
        ),
        (
            '    <div style="max-width: 600px; margin: auto; background: white; padding: 40px;'
        ),
        ('                 border-radius: 12px; border: 1px solid #e5e7eb;">'),
        f'      <h2 style="color: #4F46E5; margin-bottom: 20px;">{title}</h2>',
        f'      <p style="font-size: 16px;">{message}</p>',
        '      <div style="margin-top: 35px; text-align: center;">',
        f'        <a href="{ROADMAP_URL}"',
        (
            '           style="background-color: #4F46E5; color: white; padding: 14px 30px;'
        ),
        (
            "                  text-decoration: none; border-radius: 8px; font-weight: 600;"
        ),
        '                  font-size: 16px; display: inline-block;">',
        "          View My Roadmap",
        "        </a>",
        "      </div>",
        '      <hr style="border: 0; border-top: 1px solid #eee; margin: 40px 0 20px 0;">',
        '      <p style="font-size: 12px; color: #6b7280; text-align: center;">',
        "        This is an automated reminder from your Adaptive Goal Planner.",
        "      </p>",
        "    </div>",
        "  </body>",
        "</html>",
    ]
    return "\n".join(lines)


def send_notification_email(email: str, title: str, message: str) -> None:
    """Send an HTML email notification to the given address."""
    html_content = build_email_html(title, message)
    send_email(email, title, html_content)


def create_notification(db: Session, params: NotificationParams) -> Notification | None:
    try:
        notification = Notification(
            user_id=params.user_id,
            goal_id=params.goal_id,
            title=params.title,
            message=params.message,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        if params.send_mail and params.email:
            send_notification_email(
                email=params.email,
                title=params.title,
                message=params.message,
            )
        return notification
    except Exception as exc:
        logger.error(f"Failed to create notification for user {params.user_id}: {exc}")
        db.rollback()
        return None
