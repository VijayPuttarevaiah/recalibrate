# Tests for models/base.py
from models.base import Base


def test_base_class_exists():
    assert hasattr(Base, '__table__') or hasattr(Base, 'metadata')
