from pydantic import BaseModel

from app.schemas.character import CharacterResponse


class UpdateNicknameRequest(BaseModel):
    nickname: str


class UserInfoResponse(BaseModel):
    uid: str
    nickname: str
    email: str | None = None
    current_character: CharacterResponse
    owned_characters: list[CharacterResponse] = []
