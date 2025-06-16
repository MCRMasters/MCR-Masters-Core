from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import jwt
from jose.exceptions import JWTError

from app.core.config import settings
from app.schemas.auth.jwt import JwtTokenPayload


def create_access_token(user_id: UUID) -> str:
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = JwtTokenPayload(
        sub=str(user_id),
        typ="access",
        exp=int((datetime.now(UTC) + expires_delta).timestamp()),
    )

    encoded_token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return str(encoded_token)


def create_refresh_token(user_id: UUID) -> str:
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = JwtTokenPayload(
        sub=str(user_id),
        typ="refresh",
        exp=int((datetime.now(UTC) + expires_delta).timestamp()),
    )

    encoded_token = jwt.encode(
        payload.model_dump(),
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return str(encoded_token)


def decode_token(token: str) -> JwtTokenPayload | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None
    else:
        jwt_token_payload: JwtTokenPayload = JwtTokenPayload.model_validate(payload)
        return jwt_token_payload


def get_user_id_from_token(token: str) -> UUID | None:
    payload = decode_token(token)
    if payload:
        return UUID(payload.sub)
    return None
