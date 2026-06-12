from fastapi import APIRouter, Depends

from app.services.orchestration.session_store import (
    get_session_history
)

from app.services.security.rbac_dependency import (
    require_permission
)


router = APIRouter()


@router.get(
    "/session/history",
    dependencies=[
        Depends(
            require_permission("view_sessions")
        )
    ]
)
def session_history(
    limit: int = 100
):

    return {
        "sessions":
            get_session_history(
                limit
            )
    }