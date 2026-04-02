"""Backward-compatible re-exports. Canonical code in auth/email_verification/service.py"""

from auth.email_verification.service import *  # noqa: F401,F403
from auth.email_verification.service import (
    VerificationService,
    verification_codes,
    CODE_EXPIRY_SECONDS,
    DEFAULT_CODE_LENGTH,
)
from auth.utils.email_sender import send_email  # noqa: F401 — needed for monkeypatch compat
