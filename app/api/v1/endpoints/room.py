from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.repositories import get_room_by_number
from app.dependencies.services import get_room_service
from app.models.room import Room
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.room import RoomResponse
from app.services.room_service import RoomService

router = APIRouter()


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
):
    room = await room_service.create_room(current_user.id)

    return RoomResponse(
        name=room.name,
        room_number=room.room_number,
    )


@router.post(
    "/{room_number}/join",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def join_room(
    room: Room = Depends(get_room_by_number),
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
):
    await room_service.join_room(current_user.id, room.id)
    return BaseResponse(message="Room joined successfully")


@router.post(
    "/{room_number}/toggle-ready",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_ready(
    room: Room = Depends(get_room_by_number),
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
) -> BaseResponse:
    room_user = await room_service.toggle_ready(current_user.id, room.id)
    status_msg = "ready" if room_user.is_ready else "not ready"
    return BaseResponse(message=f"User is now {status_msg}")
