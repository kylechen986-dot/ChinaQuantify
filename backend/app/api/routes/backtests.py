from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.backtest_service import get_backtest_summary

router = APIRouter()


@router.get("/summary", response_model=ApiResponse)
def summary() -> ApiResponse:
    return ApiResponse(data=get_backtest_summary())
