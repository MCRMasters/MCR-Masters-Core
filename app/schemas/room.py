from pydantic import BaseModel


class RoomResponse(BaseModel):
    name: str
    room_number: int
