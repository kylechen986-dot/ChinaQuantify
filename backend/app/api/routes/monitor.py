from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.monitor_service import build_weekly_review, collect_watchlist_snapshot, get_monitor_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=ApiResponse)
def dashboard() -> ApiResponse:
    return ApiResponse(data=get_monitor_dashboard())


@router.post("/collect", response_model=ApiResponse)
def collect_now() -> ApiResponse:
    return ApiResponse(data=collect_watchlist_snapshot(trigger="manual"))


@router.post("/weekly-review", response_model=ApiResponse)
def weekly_review_now() -> ApiResponse:
    return ApiResponse(data=build_weekly_review(trigger="manual"))
