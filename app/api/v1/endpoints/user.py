from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_user_service
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.user import CharacterResponse, UpdateNicknameRequest, UserInfoResponse
from app.services.auth.user_service import UserService

router = APIRouter()


@router.put("/me/nickname", response_model=BaseResponse)
async def update_user_nickname(
    request: UpdateNicknameRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.update_nickname(current_user.id, request.nickname)
    return BaseResponse(message="Nickname Update Success")


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserInfoResponse:
    current_char = current_user.character
    owned = current_user.owned_characters or []

    return UserInfoResponse(
        uid=current_user.uid,
        nickname=current_user.nickname,
        email=current_user.email,
        current_character=CharacterResponse(
            code=current_char.code, name=current_char.name
        ),
        owned_characters=[
            CharacterResponse(code=ch.code, name=ch.name) for ch in owned
        ],
    )


@router.post(
    "/me/character/{character_code}",
    response_model=BaseResponse,
)
async def toggle_my_character(
    character_code: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse:
    added = await user_service.toggle_owned_character(current_user.id, character_code)
    action = "added" if added else "removed"
    return BaseResponse(message=f"Character {character_code} {action} successfully")


@router.put(
    "/me/character/{character_code}",
    response_model=BaseResponse,
)
async def set_my_current_character(
    character_code: str,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> BaseResponse:
    await user_service.set_current_character(current_user.id, character_code)
    return BaseResponse(message=f"Current character set to {character_code}")
