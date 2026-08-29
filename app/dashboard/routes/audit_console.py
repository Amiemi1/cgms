from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.services.explainability.audit_store import (
    get_audit_records
)

from app.services.security.rbac_dependency import (
    require_permission
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.persistence.audit_store import (
    PersistentAuditStore,
    get_persistent_audit_store,
)


router = APIRouter()


@router.get(
    "/audit/records",
)
def audit_records(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            require_permission("view_audit")
        ),
    ],
    audit_store: Annotated[
        PersistentAuditStore,
        Depends(
            get_persistent_audit_store
        ),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
    include_global: bool = False,
):

    if (
        include_global
        and not principal.has_permission(
            "manage_users"
        )
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Permission denied: manage_users"
            ),
        )

    return {
        "records":
            get_audit_records(
                workspace_id=(
                    principal.workspace_id
                ),
                limit=limit,
                include_global=include_global,
                audit_store=audit_store,
            )
    }
