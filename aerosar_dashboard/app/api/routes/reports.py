from typing import List

from fastapi import APIRouter, HTTPException

from app.api.schemas import ReportCreateRequest, ReportResponse, RetrievedContextResponse
from app.services.backend_service import BackendService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportResponse], summary="List reports")
def list_reports() -> List[ReportResponse]:
    return [ReportResponse.model_validate(item.model_dump()) for item in BackendService().get_reports()]


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report by id")
def get_report(report_id: str) -> ReportResponse:
    report = BackendService().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse.model_validate(report.model_dump())


@router.post("", response_model=ReportResponse, summary="Create report")
def create_report(payload: ReportCreateRequest) -> ReportResponse:
    report = payload.to_report()
    saved = BackendService().create_report(report)
    return ReportResponse.model_validate(saved.model_dump())


@router.get("/{report_id}/context", response_model=List[RetrievedContextResponse], summary="List context for report")
def get_report_context(report_id: str) -> List[RetrievedContextResponse]:
    results = BackendService().get_context_for_report(report_id)
    return [RetrievedContextResponse.model_validate(item.model_dump()) for item in results]


@router.post("/{report_id}/context", response_model=RetrievedContextResponse, summary="Add context for report")
def add_report_context(report_id: str, payload: RetrievedContextResponse) -> RetrievedContextResponse:
    context = payload.to_context()
    saved = BackendService().create_context(report_id, context)
    return RetrievedContextResponse.model_validate(saved.model_dump())
