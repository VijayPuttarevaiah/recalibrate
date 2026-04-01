import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from goals.models.task_models import Task

def test_task_notes_column_added(db_session: Session):
    """Test if the 'notes' column exists in the 'tasks' table."""
    inspector = inspect(db_session.get_bind())
    columns = [col['name'] for col in inspector.get_columns('tasks')]
    assert 'notes' in columns, "The 'notes' column is missing in the 'tasks' table."

def test_task_notes_column_nullable(db_session: Session):
    """Test if the 'notes' column is nullable."""
    inspector = inspect(db_session.get_bind())
    columns = inspector.get_columns('tasks')
    notes_column = next((col for col in columns if col['name'] == 'notes'), None)
    assert notes_column is not None, "The 'notes' column is missing in the 'tasks' table."
    assert notes_column['nullable'], "The 'notes' column should be nullable."