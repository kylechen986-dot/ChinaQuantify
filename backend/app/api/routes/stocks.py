from fastapi import APIRouter
from fastapi import HTTPException

from app.schemas.common import ApiResponse
from app.services.watchlist_service import (
    add_watch_stock,
    get_stock,
    list_industries,
    list_recommended_stocks,
    list_stocks,
    list_watch_stocks,
)

router = APIRouter()


@router.get("", response_model=ApiResponse)
def stocks(page: int = 1, page_size: int = 50, keyword: str = "", industry: str = "") -> ApiResponse:
    return ApiResponse(data=list_stocks(page=page, page_size=page_size, keyword=keyword, industry=industry))


@router.get("/industries", response_model=ApiResponse)
def industries() -> ApiResponse:
    return ApiResponse(data=list_industries())


@router.get("/recommendations", response_model=ApiResponse)
def recommendations(limit: int = 6) -> ApiResponse:
    return ApiResponse(data=list_recommended_stocks(limit=limit))


@router.get("/watchlist", response_model=ApiResponse)
def watchlist() -> ApiResponse:
    return ApiResponse(data=list_watch_stocks())


@router.post("/watchlist/{symbol}", response_model=ApiResponse)
def add_to_watchlist(symbol: str) -> ApiResponse:
    stock = add_watch_stock(symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return ApiResponse(data=stock)


@router.get("/{symbol}", response_model=ApiResponse)
def stock_detail(symbol: str) -> ApiResponse:
    stock = get_stock(symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return ApiResponse(data=stock)
