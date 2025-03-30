from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.schemas.auth.base import TokenResponse
from app.schemas.auth.google import (
    GoogleAuthParams,
    GoogleTokenRequest,
    GoogleTokenResponse,
    GoogleUserInfo,
)
from app.services.auth.user_service import UserService


class GoogleOAuthService:
    def __init__(self, session: AsyncSession, user_service: UserService | None = None):
        self.session = session
        self.user_service = user_service or UserService(session)
        self.auth_url = settings.GOOGLE_AUTH_URL
        self.token_url = settings.GOOGLE_TOKEN_URL
        self.user_info_url = settings.GOOGLE_USER_INFO_URL
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

    def get_authorization_url(self, state: str) -> str:
        params = GoogleAuthParams(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=state,
        )
        return f"{self.auth_url}?{urlencode(params.model_dump())}"

    async def get_google_token(self, code: str) -> GoogleTokenResponse:
        token_request = GoogleTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
            code=code,
            redirect_uri=self.redirect_uri,
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data=token_request.to_dict(),
            )
            response.raise_for_status()
            token_data = response.json()
            return GoogleTokenResponse.model_validate(token_data)

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers=headers,
            )
            response.raise_for_status()
            user_data = response.json()
            return GoogleUserInfo.model_validate(user_data)

    async def process_google_login(self, code: str) -> TokenResponse:
        try:
            token_info = await self.get_google_token(code)
            user_info = await self.get_user_info(token_info.access_token)

            user, is_new_user = await self.user_service.get_or_create_user(
                user_info.model_dump(),
            )

            user.last_login = datetime.now(UTC)

            user = await self.user_service.user_repository.update(user)
            await self.session.commit()

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
