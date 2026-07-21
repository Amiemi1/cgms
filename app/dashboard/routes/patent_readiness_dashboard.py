from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.patent_governance.dashboard_service import (
    PatentDashboardService,
)
from app.services.security.rbac_dependency import (
    require_permission,
)
from app.services.security.rbac_policy import (
    VIEW_PATENT_GOVERNANCE,
    VIEW_PATENT_SENSITIVE,
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

patent_access_logger = logging.getLogger(
    "cgms.security.patent_access"
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
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            require_permission(
                VIEW_PATENT_GOVERNANCE
            )
        ),
    ],
) -> HTMLResponse:
    """
    Render the authenticated Patent and IP Progress Dashboard.

    Patent governance access and sensitive-identifier access are
    separate permissions. The request cannot activate sensitive
    disclosure through query parameters or caller-provided roles.
    """
    include_sensitive = principal.has_permission(
        VIEW_PATENT_SENSITIVE
    )

    dashboard = service.build_view(
        include_sensitive=include_sensitive,
        production_access_enabled=True,
    )

    patent_access_logger.info(
        "patent_dashboard_accessed "
        "user_id=%s role=%s sensitive=%s token_id=%s",
        principal.user_id,
        principal.role,
        include_sensitive,
        principal.token_id or "not-recorded",
    )

    response = templates.TemplateResponse(
        request=request,
        name="patent_readiness_dashboard.html",
        context={
            "dashboard": dashboard,
            "principal": {
                "user_id": principal.user_id,
                "role": principal.role,
                "sensitive_access": include_sensitive,
            },
        },
    )

    response.headers.update(
        {
            "Cache-Control": (
                "no-store, no-cache, must-revalidate, "
                "private, max-age=0"
            ),
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "script-src 'none'; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "frame-ancestors 'none'; "
                "form-action 'none'"
            ),
        }
    )

    return response