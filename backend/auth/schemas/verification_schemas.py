"""Backward-compatible re-exports. Canonical code in auth/email_verification/schemas.py"""
from auth.email_verification.schemas import *  # noqa: F401,F403
from auth.email_verification.schemas import SendCodeRequest, VerifyCodeRequest
