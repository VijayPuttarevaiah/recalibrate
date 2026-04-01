"""Backward-compatible re-exports. Canonical code in auth/register/schemas.py"""
from auth.register.schemas import *  # noqa: F401,F403
from auth.register.schemas import UserCreate, UserResponse, RegisterRequest, validate_strong_password, MIN_PASSWORD_LENGTH
