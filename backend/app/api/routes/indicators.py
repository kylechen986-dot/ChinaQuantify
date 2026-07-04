from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.market_service import get_indicator_snapshots

router = APIRouter()


@router.get("/latest", response_model=ApiResponse)
def latest_indicators() -> ApiResponse:
    return ApiResponse(data=get_indicator_snapshots())
