import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from app.dependencies.services import get_google_oauth_service
from app.schemas.auth.base import AuthUrlResponse, TokenResponse
from app.services.auth.google import GoogleOAuthService

router = APIRouter()

session_tokens: dict[str, TokenResponse] = {}


@router.get("/login/google", response_model=AuthUrlResponse)
async def google_login(
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    session_id: str = str(uuid.uuid4())
    auth_url = google_service.get_authorization_url(state=session_id)
    return AuthUrlResponse(auth_url=auth_url, session_id=session_id)


@router.get(
    "/login/google/callback",
    response_class=HTMLResponse,
)
async def google_callback(
    code: str,
    state: str,
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    token_response: TokenResponse = await google_service.process_google_login(code)
    session_tokens[state] = token_response

    return HTMLResponse("""
<!DOCTYPE html>
<html>
<body>
    <script>window.close();</script>
</body>
</html>
""")


@router.get("/login/status", response_model=TokenResponse)
async def login_status(session_id: str):
    token_response: TokenResponse | None = session_tokens.get(session_id)
    if token_response is not None:
        del session_tokens[session_id]
        return token_response
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Token is not Ready.",
    )
