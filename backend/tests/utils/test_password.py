# Tests for utils/password.py
import pytest
from utils.password import hash_password, verify_password

def test_hash_and_verify_password():
    pw = "SuperSecret123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("WrongPassword", hashed)
