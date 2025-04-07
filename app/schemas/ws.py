from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WSActionType(str, Enum):
    PING = "ping"
    JOIN = "join"
    LEAVE = "leave"
    READY = "ready"

    PONG = "pong"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_READY_CHANGED = "user_ready_changed"
    GAME_STARTED = "game_started"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    action: str
    data: dict[str, Any] | None = None


class WebSocketResponse(BaseModel):
    status: Literal["success", "error"]
    action: str
    data: dict[str, Any] | None = None
    error: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class UserReadyData(BaseModel):
    user_id: UUID
    nickname: str
    is_ready: bool


class UserJoinedData(BaseModel):
    user_id: str
    nickname: str
    is_ready: bool = False


class UserLeftData(BaseModel):
    user_id: UUID


class GameStartedData(BaseModel):
    game_url: str
