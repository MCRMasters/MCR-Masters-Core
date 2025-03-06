from datetime import UTC, datetime

from pydantic import BaseModel, Field


class JwtTokenPayload(BaseModel):
    sub: str
    typ: str
    exp: int
    iat: int = Field(default_factory=lambda: int(datetime.now(UTC).timestamp()))
