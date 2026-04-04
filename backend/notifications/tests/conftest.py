from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    # refresh is a no-op by default
    db.refresh.return_value = None
    return db
