from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.services import get_room_service, get_user_service
from app.models.room import Room
from app.models.room_user import RoomUser
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.user import CharacterResponse, UpdateNicknameRequest, UserInfoResponse
from app.services.auth.user_service import UserService
from app.services.room_service import RoomService

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


@router.get(
    "/me/is-playing",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
)
async def is_user_in_playing_room(
    current_user: User = Depends(get_current_user),
    room_service: RoomService = Depends(get_room_service),
) -> BaseResponse:
    room_user: RoomUser | None = await room_service.room_user_repository.filter_one(
        user_id=current_user.id
    )
    if not room_user:
        return BaseResponse(
            message="User is not in any room", data={"in_playing_room": False}
        )

    room: Room | None = await room_service.room_repository.filter_one(
        id=room_user.room_id
    )
    print(f"[DEBUG] room={room}")

    if not room:
        return BaseResponse(message="Room not found", data={"in_playing_room": False})
    print(f"[DEBUG] is_playing={room.is_playing}, game_id={room.game_id}")

    return BaseResponse(
        message="User room status checked",
        data={"in_playing_room": room.is_playing, "game_id": room.game_id},
    )
