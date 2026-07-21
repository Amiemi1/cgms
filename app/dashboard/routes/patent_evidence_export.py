from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.patent_governance.export_service import (
    PatentEvidenceExportService,
)
from app.services.security.rbac_dependency import (
    require_permission,
)
from app.services.security.rbac_policy import (
    VIEW_PATENT_GOVERNANCE,
    VIEW_PATENT_SENSITIVE,
)


router = APIRouter(
    prefix="/patent-readiness",
    tags=["Patent and IP Governance"],
    include_in_schema=False,
)

patent_export_logger = logging.getLogger(
    "cgms.security.patent_export"
)


def get_patent_export_service() -> PatentEvidenceExportService:
    return PatentEvidenceExportService()


@router.get(
    "/evidence-package",
    response_class=Response,
    name="patent_evidence_package",
)
def export_patent_evidence_package(
    service: Annotated[
        PatentEvidenceExportService,
        Depends(get_patent_export_service),
    ],
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            require_permission(
                VIEW_PATENT_GOVERNANCE
            )
        ),
    ],
) -> Response:
    """
    Export the governed Patent and IP evidence package.

    Patent-governance permission controls package access.
    Sensitive identifiers are included only when the verified
    principal has the separate sensitive-data permission.
    """
    include_sensitive = principal.has_permission(
        VIEW_PATENT_SENSITIVE
    )

    package = service.build_package(
        include_sensitive=include_sensitive
    )

    patent_export_logger.info(
        "patent_evidence_package_exported "
        "user_id=%s role=%s sensitive=%s "
        "matter_id=%s files=%s size_bytes=%s "
        "sha256=%s token_id=%s",
        principal.user_id,
        principal.role,
        package.includes_sensitive_identifiers,
        package.matter_id,
        package.file_count,
        package.size_bytes,
        package.sha256,
        principal.token_id or "not-recorded",
    )

    response = Response(
        content=package.content,
        media_type=package.media_type,
    )

    response.headers.update(
        {
            "Content-Disposition": (
                f'attachment; filename="{package.filename}"'
            ),
            "Content-Length": str(
                package.size_bytes
            ),
            "X-CGMS-Package-SHA256": package.sha256,
            "X-CGMS-Matter-ID": package.matter_id,
            "X-CGMS-Sensitive-Identifiers": (
                "included"
                if package.includes_sensitive_identifiers
                else "masked"
            ),
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
                "default-src 'none'; "
                "object-src 'none'; "
                "base-uri 'none'; "
                "frame-ancestors 'none'; "
                "form-action 'none'"
            ),
        }
    )

    return response