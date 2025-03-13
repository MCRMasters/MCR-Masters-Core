from pydantic import BaseModel


class UpdateNicknameRequest(BaseModel):
    nickname: str


class UserInfoResponse(BaseModel):
    uid: str
    nickname: str
    email: str | None = None
