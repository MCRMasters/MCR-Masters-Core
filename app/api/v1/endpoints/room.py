from fastapi import APIRouter, Depends, status

from app.core.error import DomainErrorCode, MCRDomainError
from app.dependencies.auth import get_current_user
from app.dependencies.repositories import get_room_by_number
from app.dependencies.services import get_room_service
from app.models.room import Room
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.room import AvailableRoomResponse, RoomResponse
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


@router.get(
    "",
    response_model=list[AvailableRoomResponse],
    status_code=status.HTTP_200_OK,
)
async def get_available_rooms(
    current_user: User = Depends(get_current_user),  # noqa : ARG001
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_available_rooms()


@router.post(
    "/{room_number}/game-start",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def start_game(
    room: Room = Depends(get_room_by_number),
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
):
    if room.host_id != current_user.id:
        raise MCRDomainError(
            code=DomainErrorCode.NOT_HOST,
            message="Only the host can start the game",
            details={
                "user_id": str(current_user.id),
                "host_id": str(room.host_id),
                "room_id": str(room.id),
            },
        )

    await room_service.start_game(room.id)
    return BaseResponse(message="Game started successfully")
