from datetime import datetime

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse)
def health() -> ApiResponse:
    return ApiResponse(
        data={
            "status": "ok",
            "app": settings.app_name,
            "env": settings.app_env,
            "time": datetime.now().isoformat(timespec="seconds"),
        }
    )


@router.get("/version", response_model=ApiResponse)
def version() -> ApiResponse:
    return ApiResponse(data={"version": "0.1.0", "name": settings.app_name})
