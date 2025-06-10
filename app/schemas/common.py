from typing import Any

from pydantic import BaseModel


class BaseResponse(BaseModel):
    message: str
    data: Any | None = None
