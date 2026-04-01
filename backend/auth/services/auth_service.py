"""Backward-compatible re-exports. Canonical code lives in feature folders."""
from auth.login.service import LoginService
from auth.register.service import RegisterService
from auth.logout.service import LogoutService

# AuthService facade for backward compatibility
class AuthService:
    """Facade that delegates to feature-specific services."""
    def __init__(self, db):
        self._login = LoginService(db)
        self._register = RegisterService(db)
        self._logout = LogoutService(db)
        self.user_repo = self._login.user_repo

    def register_user(self, user_data):
        return self._register.register_user(user_data)

    def authenticate_user(self, email, password):
        return self._login.authenticate_user(email, password)

    def create_access_token(self, data, expires_delta=None):
        return self._login.create_access_token(data, expires_delta)

    def login_user(self, email, password):
        return self._login.login_user(email, password)

    def logout_user(self, token, db):
        return self._logout.logout_user(token, db)

    def get_current_user_id(self, token):
        return self._login.get_current_user_id(token)


def get_auth_service(db):
    """Lightweight factory to keep module behavior explicit for tooling."""
    return AuthService(db)