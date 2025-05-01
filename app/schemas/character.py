from pydantic import BaseModel


class CharacterResponse(BaseModel):
    code: str
    name: str
