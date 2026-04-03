# Tests for models/base.py
from core.base import Base

def test_base_class_exists():
    assert hasattr(Base, "__table__") or hasattr(Base, "metadata")
