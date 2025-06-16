from uuid import UUID

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)
from app.schemas.auth.jwt import JwtTokenPayload


class AuthService:
    def create_token_pair(self, user_id: UUID) -> tuple[str, str]:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        return access_token, refresh_token

    def create_access_token(self, user_id: UUID) -> str:
        return create_access_token(user_id)

    def create_refresh_token(self, user_id: UUID) -> str:
        return create_refresh_token(user_id)

    def verify_token(self, token: str) -> JwtTokenPayload | None:
        return decode_token(token)

    def extract_user_id(self, token: str) -> UUID | None:
        return get_user_id_from_token(token)

    def is_token_valid(self, token: str) -> bool:
        return self.verify_token(token) is not None
