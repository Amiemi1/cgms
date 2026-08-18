from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.workspace.admin import (
    activate_workspace,
    get_workspace_admin_state,
    suspend_workspace,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
    get_workspace_control_repository,
)


router = APIRouter()


@router.get("/workspace/admin")
def admin_state(
    repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return get_workspace_admin_state(repository)


@router.post("/workspace/admin/{workspace_id}/suspend")
def suspend(
    workspace_id: str,
    payload: dict[str, object],
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return suspend_workspace(
        workspace_id,
        str(
            payload.get("reason")
            or "manual_admin_action"
        ),
        updated_by_user_id=principal.user_id,
        repository=repository,
    )


@router.post("/workspace/admin/{workspace_id}/activate")
def activate(
    workspace_id: str,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return activate_workspace(
        workspace_id,
        updated_by_user_id=principal.user_id,
        repository=repository,
    )
