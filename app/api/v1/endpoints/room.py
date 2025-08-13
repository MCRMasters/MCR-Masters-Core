from fastapi import APIRouter, Depends, status

from app.core.error import DomainErrorCode, MCRDomainError
from app.dependencies.auth import get_current_user
from app.dependencies.repositories import get_room_by_number
from app.dependencies.services import get_room_service
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.room import (
    AvailableRoomResponse,
    RoomDetailResponse,
    RoomResponse,
    RoomUsersResponse,
)
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
    room = await room_service.create_room(current_user_id=current_user.id)

    return RoomResponse(
        name=room.name,
        room_number=room.room_number,
        slot_index=0,
    )


@router.post(
    "/{room_number}/join",
    response_model=RoomResponse,
    status_code=status.HTTP_200_OK,
)
async def join_room(
    room: Room = Depends(get_room_by_number),
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
):
    existing_ru = await room_service.room_user_repository.filter_one(
        user_id=current_user.id
    )
    if existing_ru:
        await room_service.leave_room(
            user_id=current_user.id, room_id=existing_ru.room_id
        )

    room_user: RoomUser = await room_service.join_room(current_user.id, room.id)

    return RoomResponse(
        name=room.name,
        room_number=room.room_number,
        slot_index=room_user.slot_index,
    )


@router.get(
    "",
    response_model=list[AvailableRoomResponse],
    status_code=status.HTTP_200_OK,
)
async def get_available_rooms(
    current_user: User = Depends(get_current_user),  # noqa : ARG001
    room_service: RoomService = Depends(get_room_service),
):
    await room_service.cleanup_rooms()
    return await room_service.get_available_rooms()


@router.get(
    "/{room_number}/users",
    response_model=RoomUsersResponse,
    status_code=status.HTTP_200_OK,
)
async def read_room_users(
    room: Room = Depends(get_room_by_number),
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_room_users(room.id)


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


@router.post(
    "/{room_number}/leave",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def leave_room(
    room: Room = Depends(get_room_by_number),
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
):
    await room_service.leave_room(current_user.id, room.id)
    return BaseResponse(message="Left room successfully")


@router.get(
    "/me",
    response_model=RoomDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_room(
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
) -> RoomDetailResponse:
    room_user: RoomUser | None = await room_service.room_user_repository.filter_one(
        user_id=current_user.id
    )
    if not room_user:
        raise MCRDomainError(
            code=DomainErrorCode.USER_NOT_IN_ROOM,
            message="User is not in any room",
            details={"user_id": str(current_user.id)},
        )

    room: Room | None = await room_service.room_repository.filter_one(
        id=room_user.room_id
    )
    if not room:
        raise MCRDomainError(
            code=DomainErrorCode.ROOM_NOT_FOUND,
            message="Room not found",
            details={"room_id": str(room_user.room_id)},
        )

    room_users_response = await room_service.get_room_users(room.id)
    users = room_users_response.users

    return RoomDetailResponse(
        room_number=room.room_number,
        name=room.name,
        is_playing=room.is_playing,
        game_id=room.game_id or "",
        users=users,
    )
