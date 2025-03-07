from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.schemas.google_oauth import (
    GoogleAuthParams,
    GoogleTokenRequest,
    GoogleTokenResponse,
    GoogleUserInfo,
)
from app.schemas.token_response import TokenResponse
from app.services.auth.user_service import get_or_create_user


class GoogleOAuthService:
    @staticmethod
    def get_authorization_url() -> str:
        params = GoogleAuthParams(
            client_id=settings.GOOGLE_CLIENT_ID,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )
        return f"{settings.GOOGLE_AUTH_URL}?{urlencode(params.model_dump())}"

    @staticmethod
    async def get_google_token(code: str) -> GoogleTokenResponse:
        token_request = GoogleTokenRequest(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            code=code,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GOOGLE_TOKEN_URL,
                data=token_request.to_dict(),
            )
            response.raise_for_status()
            token_data = response.json()
            validated_token: GoogleTokenResponse = GoogleTokenResponse.model_validate(
                token_data,
            )
            return validated_token

    @staticmethod
    async def get_user_info(access_token: str) -> GoogleUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.GOOGLE_USER_INFO_URL,
                headers=headers,
            )
            response.raise_for_status()
            user_data = response.json()
            validated_user: GoogleUserInfo = GoogleUserInfo.model_validate(user_data)
            return validated_user

    @staticmethod
    async def process_google_login(
        code: str,
        session: AsyncSession,
    ) -> TokenResponse:
        try:
            token_info = await GoogleOAuthService.get_google_token(code)
            user_info = await GoogleOAuthService.get_user_info(token_info.access_token)
            user, is_new_user = await get_or_create_user(
                session,
                user_info.model_dump(),
            )

            user.last_login = datetime.now(UTC)
            await session.commit()
            await session.refresh(user)

            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                is_new_user=is_new_user,
            )

        except httpx.HTTPError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get token from Google",
            )
