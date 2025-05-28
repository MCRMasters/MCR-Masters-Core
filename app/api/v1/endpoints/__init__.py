from fastapi import APIRouter

from app.api.v1.endpoints import auth, room, user, watch, ws_room

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(ws_room.router, prefix="/ws/room", tags=["ws"])

api_router.include_router(user.router, prefix="/user", tags=["users"])

api_router.include_router(room.router, prefix="/room", tags=["rooms"])

api_router.include_router(watch.router, prefix="/watch", tags=["watch"])
