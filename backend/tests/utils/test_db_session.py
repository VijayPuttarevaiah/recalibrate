# Tests for utils/db_session.py
from core.db_session import DBSession


def test_db_session_singleton():
    db1 = DBSession()
    db2 = DBSession()
    assert db1 is db2
    assert hasattr(db1, "engine")
    assert hasattr(db1, "SessionLocal")
