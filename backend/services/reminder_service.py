import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from models.task_models import Task
from models.user_models import User
from services.notification_service import create_notification
from utils.db_session import DBSession

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
DEADLINE_WINDOW_HOURS = 24
COMPLETED_STATUS = "completed"
REMINDER_TITLE = "Deadline Reminder"
CRON_INTERVAL_HOURS = 1


def _build_reminder_message(task_title: str) -> str:
    return f"Don't forget: Your task '{task_title}' is due within 24 hours!"


def _create_db_session() -> Session:
    """Thin wrapper so tests can patch DB creation without touching DBSession."""
    return DBSession().SessionLocal()


def check_upcoming_deadlines() -> None:
    """
    Query tasks due within the next 24 hours and create a notification
    (+ email) for each owning user. Runs as a background cron job.
    """
    db: Session = _create_db_session()
    try:
        logger.info("Cron: checking upcoming deadlines...")

        deadline_window = datetime.now() + timedelta(hours=DEADLINE_WINDOW_HOURS)

        upcoming_tasks = (
            db.query(Task)
            .filter(Task.due_date <= deadline_window, Task.status != COMPLETED_STATUS)
            .all()
        )

        for task in upcoming_tasks:
            user = db.query(User).filter(User.id == task.user_id).first()
            if not user:
                logger.warning(f"Cron: no user found for task {task.id}, skipping.")
                continue

            create_notification(
                db=db,
                user_id=user.id,
                title=REMINDER_TITLE,
                message=_build_reminder_message(task.title),
                send_mail=True,
                email=user.email,
            )

        logger.info(f"Cron: dispatched {len(upcoming_tasks)} notification(s).")

    except Exception as exc:
        logger.error(f"Cron error: {exc}")

    finally:
        db.close()


def start_cron_jobs() -> BackgroundScheduler:
    """Register and start all background scheduled jobs."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_deadlines, "interval", hours=CRON_INTERVAL_HOURS)
    scheduler.start()
    logger.info("APScheduler: background jobs started successfully.")
    return scheduler