"""Backward-compatible re-exports. Canonical code in auth/password_reset/service.py"""

from auth.password_reset.service import *  # noqa: F401,F403
from auth.password_reset.service import (
    PasswordResetService,
    reset_codes,
    DEFAULT_CODE_LENGTH,
    RESET_CODE_EXPIRY_SECONDS,
)
from auth.utils.email_sender import send_email  # noqa: F401 — needed for monkeypatch compat
