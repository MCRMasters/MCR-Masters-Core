from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import decode_token, get_user_id_from_token
from app.schemas.auth.jwt import JwtTokenPayload


@pytest.fixture
def valid_access_token(user_id):
    expires_delta = timedelta(minutes=15)
    payload = JwtTokenPayload(
        sub=str(user_id),
        typ="access",
        exp=int((datetime.now(UTC) + expires_delta).timestamp()),
    )
    token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
def expired_token(user_id):
    expires_delta = timedelta(minutes=-15)
    payload = JwtTokenPayload(
        sub=str(user_id),
        typ="access",
        exp=int((datetime.now(UTC) + expires_delta).timestamp()),
    )
    token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


@pytest.fixture
def invalid_token():
    return "invalid.token.string"


def test_decode_token_with_valid_token(valid_access_token, user_id):
    payload = decode_token(valid_access_token)

    assert payload is not None
    assert payload.sub == str(user_id)
    assert payload.typ == "access"
    assert isinstance(payload.exp, int)
    assert isinstance(payload.iat, int)


def test_decode_token_with_expired_token(expired_token):
    payload = decode_token(expired_token)

    assert payload is None


def test_decode_token_with_invalid_token(invalid_token):
    payload = decode_token(invalid_token)

    assert payload is None


def test_get_user_id_from_token_with_valid_token(valid_access_token, user_id):
    extracted_user_id = get_user_id_from_token(valid_access_token)

    assert extracted_user_id is not None
    assert extracted_user_id == user_id


def test_get_user_id_from_token_with_expired_token(expired_token):
    extracted_user_id = get_user_id_from_token(expired_token)

    assert extracted_user_id is None


def test_get_user_id_from_token_with_invalid_token(invalid_token):
    extracted_user_id = get_user_id_from_token(invalid_token)

    assert extracted_user_id is None


def test_get_user_id_from_token_with_invalid_uuid(mocker):
    mocker.patch(
        "app.core.security.decode_token",
        return_value=None,
    )

    invalid_token = "token.with.invalid.uuid"

    extracted_user_id = get_user_id_from_token(invalid_token)
    assert extracted_user_id is None
