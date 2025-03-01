from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.auth_url_response import AuthUrlResponse
from app.schemas.token_response import TokenResponse
from app.services.auth.google import GoogleOAuthService

router = APIRouter()


@router.get("/login/google", response_model=AuthUrlResponse)
async def google_login():
    auth_url = GoogleOAuthService.get_authorization_url()
    return AuthUrlResponse(auth_url=auth_url)


@router.get("/login/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    session: AsyncSession = Depends(get_session),
):
    return await GoogleOAuthService.process_google_login(code, session)
