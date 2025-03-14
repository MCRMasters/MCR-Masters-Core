from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.dependencies.services import get_user_service
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.user import UpdateNicknameRequest, UserInfoResponse
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
    return UserInfoResponse(
        uid=current_user.uid,
        nickname=current_user.nickname,
        email=current_user.email,
    )
