import asyncio
from contextlib import suppress

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.internal.endpoints import internal_router
from app.api.v1.endpoints import api_router
from app.core.config import settings
from app.core.error import DomainErrorCode, MCRDomainError
from app.schemas.common import BaseResponse


async def cleanup_task() -> None:
    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="MCRMasters-BE",
    description="A FastAPI backend application for MCRMasters",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


app.include_router(internal_router, prefix="/internal")


@app.on_event("startup")
async def on_startup() -> None:
    cleanup = asyncio.create_task(cleanup_task())
    app.state.cleanup_task = cleanup


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app.state.cleanup_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.cleanup_task


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> BaseResponse:
    return BaseResponse(message="healthy")


@app.exception_handler(MCRDomainError)
async def mcr_domain_error_handler(
    _request: Request,
    exc: MCRDomainError,
) -> JSONResponse:
    domain_error_code_mapper = {
        DomainErrorCode.NICKNAME_ALREADY_SET: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.USER_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        DomainErrorCode.INVALID_UID: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DomainErrorCode.INVALID_NICKNAME: status.HTTP_422_UNPROCESSABLE_ENTITY,
        DomainErrorCode.USER_ALREADY_IN_ROOM: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.ROOM_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        DomainErrorCode.ROOM_IS_FULL: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.ROOM_ALREADY_PLAYING: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.ROOM_NOT_PLAYING: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.NOT_ENOUGH_PLAYERS: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.PLAYERS_NOT_READY: status.HTTP_400_BAD_REQUEST,
        DomainErrorCode.NOT_HOST: status.HTTP_403_FORBIDDEN,
    }
    status_code = domain_error_code_mapper.get(
        exc.code,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "detail": exc.message,
                "code": exc.code,
                "error_details": exc.details,
            }
        ),
    )
