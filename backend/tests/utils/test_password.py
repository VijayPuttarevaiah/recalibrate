# Tests for utils/password.py
import pytest
from backend.utils import password

def test_hash_and_verify_password():
    pw = "SuperSecret123!"
    hashed = password.hash_password(pw)
    assert hashed != pw
    assert password.verify_password(pw, hashed)
    assert not password.verify_password("WrongPassword", hashed)
