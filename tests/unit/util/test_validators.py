import pytest

from app.core.error import DomainErrorCode, MCRDomainError


@pytest.mark.asyncio
async def test_validate_nickname_whitespace(mocker):
    from app.util.validators import validate_nickname

    with pytest.raises(MCRDomainError) as exc_info:
        validate_nickname("   ")

    assert exc_info.value.code == DomainErrorCode.INVALID_NICKNAME
    assert "whitespace" in exc_info.value.message


@pytest.mark.asyncio
async def test_validate_nickname_too_long(mocker):
    from app.util.validators import validate_nickname

    long_nickname = "VeryLongNickname1234"

    with pytest.raises(MCRDomainError) as exc_info:
        validate_nickname(long_nickname)

    assert exc_info.value.code == DomainErrorCode.INVALID_NICKNAME
    assert "10 characters or less" in exc_info.value.message
    assert exc_info.value.details["length"] > 10
