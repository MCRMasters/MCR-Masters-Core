from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.dependencies.services import get_google_oauth_service
from app.schemas.auth.base import TokenResponse
from app.services.auth.google import GoogleOAuthService

router = APIRouter()


@router.websocket("/login/google")
async def google_login_ws(
    websocket: WebSocket,
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            match action:
                case "get_oauth_url":
                    auth_url: str = google_service.get_authorization_url()
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
                    token: TokenResponse = await google_service.process_google_login(
                        code=code,
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
