from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.patent_governance.dashboard_service import (
    PatentDashboardService,
)


_TEMPLATE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "templates"
)

templates = Jinja2Templates(
    directory=str(_TEMPLATE_DIRECTORY)
)


router = APIRouter(
    prefix="/patent-readiness",
    tags=["Patent and IP Governance"],
    include_in_schema=False,
)


def get_patent_dashboard_service() -> PatentDashboardService:
    return PatentDashboardService()


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    name="patent_readiness_dashboard",
)
def patent_readiness_dashboard(
    request: Request,
    service: Annotated[
        PatentDashboardService,
        Depends(get_patent_dashboard_service),
    ],
) -> HTMLResponse:
    """
    Render the internal Patent and IP Progress Dashboard.

    Sensitive filing identifiers are always masked in PIP-005.
    The production application must not register this router
    until PIP-006 authentication and confidentiality controls
    have been completed and validated.
    """
    dashboard = service.build_view(
        include_sensitive=False
    )

    return templates.TemplateResponse(
        request=request,
        name="patent_readiness_dashboard.html",
        context={
            "dashboard": dashboard,
        },
    )