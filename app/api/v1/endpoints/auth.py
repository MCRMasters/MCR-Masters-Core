from fastapi import APIRouter, Depends

from app.dependencies.services import get_google_oauth_service
from app.schemas.auth.base import AuthUrlResponse, TokenResponse
from app.services.auth.google import GoogleOAuthService

router = APIRouter()


@router.get("/login/google", response_model=AuthUrlResponse)
async def google_login(
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    auth_url = google_service.get_authorization_url()
    return AuthUrlResponse(auth_url=auth_url)


@router.get("/login/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    return await google_service.process_google_login(code)
