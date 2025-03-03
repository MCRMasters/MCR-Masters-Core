from fastapi import APIRouter

from app.api.v1.endpoints import auth, ws_auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(ws_auth.router, prefix="/ws/auth", tags=["ws"])
