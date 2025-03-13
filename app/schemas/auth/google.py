from pydantic import BaseModel, HttpUrl


class GoogleTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None
    token_type: str | None = None
    id_token: str | None = None


class GoogleUserInfo(BaseModel):
    email: str
    verified_email: bool | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: HttpUrl | None = None
    locale: str | None = None


class GoogleAuthParams(BaseModel):
    client_id: str
    response_type: str = "code"
    redirect_uri: str
    scope: str = "openid email profile"
    access_type: str = "offline"
    prompt: str = "consent"


class GoogleTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str
    grant_type: str = "authorization_code"

    def to_dict(self) -> dict[str, str]:
        return {str(k): str(v) for k, v in self.model_dump(exclude_none=True).items()}
