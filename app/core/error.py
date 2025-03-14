from enum import Enum
from typing import Any


class DomainErrorCode(str, Enum):
    INVALID_UID = "INVALID_UID"
    INVALID_NICKNAME = "INVALID_NICKNAME"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    NICKNAME_ALREADY_SET = "NICKNAME_ALREADY_SET"
    UID_CREATE_FAILED = "UID_CREATE_FAILED"


class MCRDomainError(Exception):
    def __init__(
        self,
        code: DomainErrorCode,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message or code.name
        self.details = details or {}
        super().__init__(self.message)
