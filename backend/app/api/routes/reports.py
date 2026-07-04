from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.report_service import get_latest_report, list_reports

router = APIRouter()


@router.get("", response_model=ApiResponse)
def reports() -> ApiResponse:
    return ApiResponse(data=list_reports())


@router.get("/latest", response_model=ApiResponse)
def latest_report() -> ApiResponse:
    return ApiResponse(data=get_latest_report())
