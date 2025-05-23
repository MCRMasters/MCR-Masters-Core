from enum import Enum
from typing import Any


class DomainErrorCode(str, Enum):
    INVALID_UID = "INVALID_UID"
    INVALID_NICKNAME = "INVALID_NICKNAME"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    NICKNAME_ALREADY_SET = "NICKNAME_ALREADY_SET"
    UID_CREATE_FAILED = "UID_CREATE_FAILED"
    USER_ALREADY_IN_ROOM = "USER_ALREADY_IN_ROOM"
    ROOM_NOT_FOUND = "ROOM_NOT_FOUND"
    ROOM_IS_FULL = "ROOM_IS_FULL"
    ROOM_ALREADY_PLAYING = "ROOM_ALREADY_PLAYING"
    ROOM_NOT_PLAYING = "ROOM_NOT_PLAYING"
    NOT_ENOUGH_PLAYERS = "NOT_ENOUGH_PLAYERS"
    PLAYERS_NOT_READY = "PLAYERS_NOT_READY"
    NOT_HOST = "NOT_HOST"
    USER_NOT_IN_ROOM = "USER_NOT_IN_ROOM"
    CHARACTER_NOT_OWNED = "CHARACTER_NOT_OWNED"
    CHARACTER_NOT_FOUND = "CHARACTER_NOT_FOUND"


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
