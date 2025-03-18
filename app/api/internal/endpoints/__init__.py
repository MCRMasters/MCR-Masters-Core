from fastapi import APIRouter

from app.api.internal.endpoints import game_server

internal_router = APIRouter()

internal_router.include_router(game_server.router, prefix="/game-server")
