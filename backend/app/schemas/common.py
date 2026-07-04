from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = ""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
