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
from app.services.auth.browser_session_dependency import (
    require_browser_permission,
)
from app.services.programme_progress.registry import (
    ProgrammeProgressRegistry,
)
from app.services.security.rbac_policy import (
    VIEW_DASHBOARD,
)


_TEMPLATE_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "templates"
)

templates = Jinja2Templates(
    directory=str(_TEMPLATE_DIRECTORY)
)

router = APIRouter(
    tags=["Programme Progress Dashboard"],
    include_in_schema=False,
)

progress_access_logger = logging.getLogger(
    "cgms.security.programme_progress"
)


def get_programme_progress_registry(
) -> ProgrammeProgressRegistry:
    return ProgrammeProgressRegistry()


@router.get(
    "/progress",
    response_class=HTMLResponse,
    name="programme_progress_dashboard",
)
def programme_progress_dashboard(
    request: Request,
    registry: Annotated[
        ProgrammeProgressRegistry,
        Depends(
            get_programme_progress_registry
        ),
    ],
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            require_browser_permission(
                VIEW_DASHBOARD
            )
        ),
    ],
) -> HTMLResponse:
    """
    Render the authenticated CGMS Programme Progress Dashboard.
    """
    dashboard = registry.build_view()

    progress_access_logger.info(
        "programme_progress_dashboard_accessed "
        "user_id=%s role=%s token_id=%s",
        principal.user_id,
        principal.role,
        principal.token_id or "not-recorded",
    )

    response = templates.TemplateResponse(
        request=request,
        name=(
            "programme_progress_dashboard.html"
        ),
        context={
            "dashboard": dashboard,
            "principal": {
                "user_id": principal.user_id,
                "role": principal.role,
            },
        },
    )

    response.headers.update(
        {
            "Cache-Control": (
                "no-store, no-cache, "
                "must-revalidate, private, max-age=0"
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
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none'"
            ),
        }
    )

    return response
