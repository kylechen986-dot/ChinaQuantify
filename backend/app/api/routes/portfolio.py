from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.portfolio_service import get_portfolio_overview

router = APIRouter()


@router.get("/overview", response_model=ApiResponse)
def overview() -> ApiResponse:
    return ApiResponse(data=get_portfolio_overview())
