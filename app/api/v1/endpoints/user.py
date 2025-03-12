from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.base_response import BaseResponse
from app.schemas.user import UpdateNicknameRequest
from app.services.auth.user_service import UserService

router = APIRouter()


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


@router.put("/me/nickname", response_model=BaseResponse)
async def update_user_nickname(
    request: UpdateNicknameRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    await user_service.update_nickname(current_user.id, request.nickname)
    await user_service.session.commit()
    return BaseResponse(message="Nickname Update Success")
