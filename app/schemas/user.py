from pydantic import BaseModel, Field


class UpdateNicknameRequest(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=10)


class UserResponse(BaseModel):
    uid: str
    nickname: str
    email: str | None = None
