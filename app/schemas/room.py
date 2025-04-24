from pydantic import BaseModel


class RoomResponse(BaseModel):
    name: str
    room_number: int
    slot_index: int


class RoomUserResponse(BaseModel):
    nickname: str
    user_uid: str
    is_ready: bool
    slot_index: int


class AvailableRoomResponse(BaseModel):
    name: str
    room_number: int
    max_users: int
    current_users: int
    host_uid: str
    host_nickname: str
    users: list[RoomUserResponse]


class RoomUsersResponse(BaseModel):
    host_uid: str
    users: list[RoomUserResponse]
