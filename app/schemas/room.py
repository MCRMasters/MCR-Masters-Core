from pydantic import BaseModel


class RoomResponse(BaseModel):
    name: str
    room_number: int


class RoomUserResponse(BaseModel):
    nickname: str
    is_ready: bool


class AvailableRoomResponse(BaseModel):
    name: str
    room_number: int
    max_users: int
    current_users: int
    host_nickname: str
    users: list[RoomUserResponse]
