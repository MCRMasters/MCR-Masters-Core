from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.token_response import TokenResponse
from app.services.auth.google import GoogleOAuthService

router = APIRouter()


@router.websocket("/login/google")
async def google_login_ws(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_session),
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            match action:
                case "get_oauth_url":
                    auth_url: str = GoogleOAuthService.get_authorization_url()
                    await websocket.send_json(
                        {
                            "action": "oauth_url",
                            "auth_url": auth_url,
                        },
                    )
                case "auth":
                    if not (code := data.get("code")):
                        await websocket.send_json(
                            {
                                "error": "No code in auth",
                            },
                        )
                        continue
                    token: TokenResponse = (
                        await GoogleOAuthService.process_google_login(
                            code=code,
                            session=session,
                        )
                    )
                    await websocket.send_json(
                        {
                            "action": "auth_success",
                            "access_token": token.access_token,
                            "refresh_token": token.refresh_token,
                            "is_new_user": token.is_new_user,
                            "token_type": token.token_type,
                        },
                    )
                case _:
                    await websocket.send_json(
                        {
                            "error": f"Invalid action: {action}",
                        },
                    )
    except WebSocketDisconnect:
        print("[google_login_ws] WebSocket disconnected.")
    except Exception as e:
        await websocket.send_json(
            {
                "error": str(e),
            },
        )
        await websocket.close()
