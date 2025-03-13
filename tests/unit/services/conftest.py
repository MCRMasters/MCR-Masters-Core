import uuid

import pytest

from app.models.user import User
from app.schemas.auth.base import TokenResponse


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def test_users():
    return [
        User(
            id=uuid.uuid4(),
            uid="100000000",
            nickname="TestUser1",
            email="test1@example.com",
        ),
        User(
            id=uuid.uuid4(),
            uid="200000000",
            nickname="TestUser2",
            email="test2@example.com",
        ),
        User(
            id=uuid.uuid4(),
            uid="300000000",
            nickname="",
            email="new@example.com",
        ),
    ]


@pytest.fixture
def mock_token_response():
    return TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        is_new_user=True,
    )
