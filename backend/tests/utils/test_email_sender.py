# Tests for utils/email_sender.py
import pytest
from backend.utils import email_sender
import smtplib

import os
import types

def test_send_email(monkeypatch):
    # Patch smtplib.SMTP to avoid real email sending
    class DummySMTP:
        def __init__(self, *a, **kw): pass
        def starttls(self): pass
        def login(self, user, pw): pass
        def send_message(self, msg):
            assert msg['To'] == 'to@example.com'
            assert msg['Subject'] == 'Test Subject'
            assert 'Test Body' in msg.as_string()
        def __enter__(self): return self
        def __exit__(self, *a): pass
    monkeypatch.setattr(smtplib, 'SMTP', DummySMTP)
    monkeypatch.setattr(email_sender.config, 'config', {
        'email': {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_user': 'user@example.com',
            'smtp_password': 'password',
        }
    })
    email_sender.send_email('to@example.com', 'Test Subject', 'Test Body')
