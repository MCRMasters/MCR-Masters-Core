from pydantic import BaseModel


class UpdateNicknameRequest(BaseModel):
    nickname: str
