from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.market_service import get_market_overview, get_symbols

router = APIRouter()


@router.get("/symbols", response_model=ApiResponse)
def list_symbols() -> ApiResponse:
    return ApiResponse(data=get_symbols())


@router.get("/overview", response_model=ApiResponse)
def market_overview() -> ApiResponse:
    return ApiResponse(data=get_market_overview())
