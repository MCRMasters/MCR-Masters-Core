import re

from app.core.error import DomainErrorCode, MCRDomainError


def validate_uid(uid: str) -> str:
    if not re.match(r"^[1-9]\d{8}$", uid):
        raise MCRDomainError(
            code=DomainErrorCode.INVALID_UID,
            message="UID must be a 9-digit number",
            details={
                "uid": uid,
            },
        )
    return uid


def validate_nickname(nickname: str) -> str:
    if nickname == "":
        return nickname

    if nickname.isspace():
        raise MCRDomainError(
            code=DomainErrorCode.INVALID_NICKNAME,
            message="Nickname cannot consist only of whitespace",
            details={
                "nickname": nickname,
            },
        )

    if len(nickname) > 10:
        raise MCRDomainError(
            code=DomainErrorCode.INVALID_NICKNAME,
            message="Nickname must be 10 characters or less",
            details={
                "nickname": nickname,
                "length": len(nickname),
            },
        )

    if not re.match(r"^[a-zA-Z0-9가-힣]+$", nickname):
        raise MCRDomainError(
            code=DomainErrorCode.INVALID_NICKNAME,
            message="Nickname can only contain English, numbers, and Korean",
            details={
                "nickname": nickname,
            },
        )

    return nickname
