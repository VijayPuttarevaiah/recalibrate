import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

pytest_plugins = [
    "tests.fixtures.db_fixtures",
    "tests.fixtures.auth_fixtures",
]
