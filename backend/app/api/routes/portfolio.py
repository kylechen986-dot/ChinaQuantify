from fastapi import APIRouter
from fastapi import HTTPException

from app.schemas.common import ApiResponse
from app.services.portfolio_service import get_portfolio_overview, get_stock_cashflows

router = APIRouter()


@router.get("/overview", response_model=ApiResponse)
def overview() -> ApiResponse:
    return ApiResponse(data=get_portfolio_overview())


@router.get("/stocks/{symbol}/cashflows", response_model=ApiResponse)
def stock_cashflows(symbol: str) -> ApiResponse:
    detail = get_stock_cashflows(symbol)
    if detail is None:
        raise HTTPException(status_code=404, detail="Position not found")
    return ApiResponse(data=detail)
