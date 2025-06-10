from fastapi import APIRouter, Depends, status

from app.dependencies.repositories import get_room_by_game_id
from app.dependencies.services import get_room_service
from app.models.room import Room
from app.schemas.common import BaseResponse
from app.services.room_service import RoomService

router = APIRouter(tags=["game_server"])


@router.post(
    "/rooms/{game_id}/end-game",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def end_game(
    room: Room = Depends(get_room_by_game_id),
    room_service: RoomService = Depends(get_room_service),
):
    await room_service.end_game(room.id)
    return BaseResponse(message="Game ended successfully")
