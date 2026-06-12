from fastapi import APIRouter, Depends

from app.services.explainability.audit_store import (
    get_audit_records
)

from app.services.security.rbac_dependency import (
    require_permission
)


router = APIRouter()


@router.get(
    "/audit/records",
    dependencies=[
        Depends(
            require_permission("view_audit")
        )
    ]
)
def audit_records(
    limit: int = 50
):

    return {
        "records":
            get_audit_records(
                limit
            )
    }