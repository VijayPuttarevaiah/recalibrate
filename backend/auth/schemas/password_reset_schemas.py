"""Backward-compatible re-exports. Canonical code in auth/password_reset/schemas.py"""

from auth.password_reset.schemas import *  # noqa: F401,F403
from auth.register.schemas import validate_strong_password  # noqa: F401
