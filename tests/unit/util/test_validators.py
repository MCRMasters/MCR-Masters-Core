import pytest

from app.core.error import DomainErrorCode, MCRDomainError
from app.util.validators import validate_nickname, validate_uid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_uid",
    [
        "123456789",
        "987654321",
        "100000000",
        "999999999",
    ],
)
async def test_validate_uid_valid(valid_uid):
    result = validate_uid(valid_uid)
    assert result == valid_uid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_uid",
    [
        "12345678",
        "1234567890",
        "0123456789",
        "abcdefghi",
        "123abc456",
        " 123456789",
    ],
)
async def test_validate_uid_invalid(invalid_uid):
    with pytest.raises(MCRDomainError) as exc_info:
        validate_uid(invalid_uid)

    assert exc_info.value.code == DomainErrorCode.INVALID_UID
    assert exc_info.value.details["uid"] == invalid_uid


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_nickname",
    [
        "User123",
        "사용자123",
        "테스트User",
        "a",
        "닉네임테스트",
        "UserTest",
        "12345",
        "",
    ],
)
async def test_validate_nickname_valid(valid_nickname):
    result = validate_nickname(valid_nickname)
    assert result == valid_nickname


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_nickname",
    [
        "User!123",
        "User 123",
        "사용자_123",
        "User@Test",
        "#유저123",
        "VeryLongNickname1234",
        " ",
        "   ",
        "\t",
        "\n",
        " \t \n",
    ],
)
async def test_validate_nickname_invalid(invalid_nickname):
    with pytest.raises(MCRDomainError) as exc_info:
        validate_nickname(invalid_nickname)

    assert exc_info.value.code == DomainErrorCode.INVALID_NICKNAME
    assert exc_info.value.details["nickname"] == invalid_nickname

    if len(invalid_nickname) > 10:
        assert "length" in exc_info.value.details
        assert exc_info.value.details["length"] > 10
