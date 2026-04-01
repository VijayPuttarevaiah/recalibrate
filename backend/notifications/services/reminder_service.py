import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from goals.models.task_models import Task
from auth.models.user_models import User
from notifications.services.notification_service import create_notification, NotificationParams
from core.db_session import DBSession

logger = logging.getLogger(__name__)

# -- Constants -----------------------------------------------------------------
DEADLINE_WINDOW_HOURS = 24
COMPLETED_STATUS = "completed"
CRON_INTERVAL_HOURS = 1

REMINDER_TITLE  = "Deadline Reminder"
OVERDUE_TITLE   = "Task Overdue"
COMPLETED_TITLE = "Task Completed"


# -- Message builders ----------------------------------------------------------

def _build_reminder_message(task_title: str) -> str:
    return f"Don't forget: Your task '{task_title}' is due within 24 hours!"


def _build_overdue_message(task_title: str) -> str:
    return f"Your task '{task_title}' is overdue. Please complete it as soon as possible."


def _build_completed_message(task_title: str) -> str:
    return f"Congratulations! You have completed the task '{task_title}'. Keep it up!"


# -- DB helper -----------------------------------------------------------------

def _create_db_session() -> Session:
    """Thin wrapper so tests can patch DB creation without touching DBSession."""
    return DBSession().SessionLocal()


# -- Notification helpers ------------------------------------------------------

def _notify_task_group(db, tasks, title_fn, message_fn, title):
    for task in tasks:
        user = db.query(User).filter(User.id == task.goal.user_id).first()
        if not user:
            logger.warning(f"Cron: no user found for task {task.id}, skipping.")
            continue
        params = NotificationParams(
            user_id=user.id,
            goal_id=task.goal_id,
            title=title,
            message=message_fn(task.title),
            send_mail=True,
            email=user.email,
        )
        create_notification(db=db, params=params)


def _fetch_upcoming_tasks(db: Session, now: datetime) -> list[Task]:
    return (
        db.query(Task)
        .filter(
            Task.due_date > now,
            Task.due_date <= now + timedelta(hours=DEADLINE_WINDOW_HOURS),
            Task.status != COMPLETED_STATUS,
        )
        .all()
    )


def _fetch_overdue_tasks(db: Session, now: datetime) -> list[Task]:
    return (
        db.query(Task)
        .filter(
            Task.due_date <= now,
            Task.status != COMPLETED_STATUS,
        )
        .all()
    )


def _fetch_completed_tasks(db: Session) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.status == COMPLETED_STATUS)
        .all()
    )


def _log_notification_summary(upcoming_tasks: list[Task], overdue_tasks: list[Task], completed_tasks: list[Task]) -> None:
    logger.info(
        "Cron: upcoming=%s, overdue=%s, completed=%s",
        len(upcoming_tasks),
        len(overdue_tasks),
        len(completed_tasks),
    )


# -- Main cron function --------------------------------------------------------

def check_upcoming_deadlines() -> None:
    """
    Runs on every cron tick and dispatches three types of notifications:

    1. Upcoming  — tasks due within the next 24 h that are not completed
    2. Overdue   — tasks whose due date has already passed and are not completed
    3. Completed — tasks marked completed within the last cron interval (1 h)
    """
    db: Session = _create_db_session()
    try:
        now = datetime.now()
        logger.info("Cron: checking task states for notifications...")

        # 1. Upcoming tasks
        upcoming_tasks = _fetch_upcoming_tasks(db, now)
        _notify_task_group(
            db,
            upcoming_tasks,
            None,
            _build_reminder_message,
            REMINDER_TITLE,
        )

        # 2. Overdue tasks
        overdue_tasks = _fetch_overdue_tasks(db, now)
        _notify_task_group(
            db,
            overdue_tasks,
            None,
            _build_overdue_message,
            OVERDUE_TITLE,
        )

        # 3. Recently completed tasks
        completed_tasks = _fetch_completed_tasks(db)
        _notify_task_group(
            db,
            completed_tasks,
            None,
            _build_completed_message,
            COMPLETED_TITLE,
        )
        _log_notification_summary(upcoming_tasks, overdue_tasks, completed_tasks)

    except Exception as exc:
        logger.error(f"Cron error: {exc}")

    finally:
        db.close()


def start_cron_jobs() -> None:
    """No-op: scheduling is handled by the system cron job."""
    logger.info("Cron: scheduling delegated to system cron — no APScheduler needed.")
