from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.room import RoomUserResponse


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
    USER_LIST = "user_list"


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
    user_uid: str
    is_ready: bool


class UserJoinedData(BaseModel):
    user_uid: str
    nickname: str
    slot_index: int
    is_ready: bool = False


class UserLeftData(BaseModel):
    user_uid: str


class GameStartedData(BaseModel):
    game_url: str


class UserListData(BaseModel):
    users: list[RoomUserResponse]
