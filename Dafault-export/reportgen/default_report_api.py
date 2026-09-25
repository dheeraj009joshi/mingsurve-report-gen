"""FastAPI routes for the default Design Element Appeal report.

Add ``Dafault-export`` to the API process path, then mount the router:

    from reportgen.default_report_api import router
    app.include_router(router, prefix="/api/v1")
"""

from __future__ import annotations

import io
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from reportgen.default_report import DefaultReportError, create_default_report

router = APIRouter(prefix="/reports", tags=["reports"])


class AppealReportBody(BaseModel):
    analysis: Dict[str, Any] = Field(..., description="analysis_data.json contents")
    study: Optional[Dict[str, Any]] = Field(None, description="Optional study_data.json contents")
    study_type: Optional[str] = Field(
        None,
        description="layer, grid, text, or hybrid. Read from the analysis when omitted.",
    )
    download_images: bool = True


def _stream(report):
    headers = {"Content-Disposition": f'attachment; filename="{report.filename}"'}
    return StreamingResponse(io.BytesIO(report.content), media_type=report.media_type, headers=headers)


@router.post("/appeal")
def create_appeal_report(body: AppealReportBody):
    """Build the default appeal deck from analysis JSON already held by the API."""
    try:
        report = create_default_report(
            body.analysis,
            study=body.study,
            download_images=body.download_images,
            study_type=body.study_type,
        )
    except DefaultReportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _stream(report)


@router.post("/appeal/upload")
async def create_appeal_report_upload(
    analysis: UploadFile = File(..., description="analysis_data.json"),
    study: Optional[UploadFile] = File(None, description="Optional study_data.json"),
    logo: Optional[UploadFile] = File(None, description="Optional brand logo"),
    study_type: Optional[str] = Form(None, description="layer, grid, text, or hybrid"),
    download_images: bool = Form(True),
):
    """Build the default appeal deck from uploaded analysis, study, and logo files."""
    analysis_bytes = await analysis.read()
    study_bytes = await study.read() if study is not None else None
    logo_bytes = await logo.read() if logo is not None else None
    try:
        report = create_default_report(
            analysis_bytes,
            study=study_bytes or None,
            logo=logo_bytes or None,
            download_images=download_images,
            study_type=study_type,
        )
    except DefaultReportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _stream(report)
