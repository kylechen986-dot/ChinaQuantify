from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.strategy_service import get_strategy_signals

router = APIRouter()


@router.get("/signals", response_model=ApiResponse)
def list_signals() -> ApiResponse:
    return ApiResponse(data=get_strategy_signals())
