from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.report_service import get_latest_report, get_report, list_reports

router = APIRouter()


@router.get("", response_model=ApiResponse)
def reports() -> ApiResponse:
    return ApiResponse(data=list_reports())


@router.get("/latest", response_model=ApiResponse)
def latest_report() -> ApiResponse:
    return ApiResponse(data=get_latest_report())


@router.get("/{report_id}", response_model=ApiResponse)
def report_detail(report_id: int) -> ApiResponse:
    return ApiResponse(data=get_report(report_id))
