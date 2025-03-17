from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_room_service
from app.models.user import User
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
