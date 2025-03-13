from pydantic import BaseModel


class AuthUrlResponse(BaseModel):
    auth_url: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_new_user: bool
    token_type: str = "bearer"
