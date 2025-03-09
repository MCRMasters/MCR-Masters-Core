from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UpdateNicknameRequest, UserResponse
from app.services.auth.user_service import update_nickname

router = APIRouter()


@router.put("/me/nickname", response_model=UserResponse)
async def update_user_nickname(
    request: UpdateNicknameRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await update_nickname(session, current_user.id, request.nickname)
    await session.commit()
    return UserResponse(
        uid=user.uid,
        nickname=user.nickname,
        email=user.email,
    )
