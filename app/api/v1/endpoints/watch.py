from fastapi import APIRouter, Depends, status
from httpx import AsyncClient

from app.core.config import settings
from app.dependencies.services import get_room_service
from app.schemas.watch import WatchGame, WatchGameUser
from app.services.room_service import RoomService

router = APIRouter()


@router.get(
    "",
    response_model=list[WatchGame],
    status_code=status.HTTP_200_OK,
)
async def get_available_watch_games(
    room_service: RoomService = Depends(get_room_service),
) -> list[WatchGame]:
    await room_service.cleanup_rooms()
    async with AsyncClient() as client:
        response = await client.get(
            f"{settings.GAME_SERVER_URL}/api/v1/games/watch",
            timeout=5.0,
        )
        response.raise_for_status()
        raw_games = response.json()

    watch_games: list[WatchGame] = []
    for raw in raw_games:
        users = [WatchGameUser(**u) for u in raw.get("users", [])]
        watch_games.append(
            WatchGame(
                game_id=raw["game_id"],
                start_time=raw["start_time"],
                users=users,
            )
        )
    return watch_games
