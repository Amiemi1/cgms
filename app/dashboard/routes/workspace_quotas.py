from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
    get_workspace_control_repository,
)
from app.services.workspace.quotas import (
    get_workspace_quota,
    get_workspace_quotas,
    set_workspace_quota,
)


router = APIRouter()


@router.get("/workspace/quotas")
def all_quotas(
    repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return get_workspace_quotas(repository)


@router.get("/workspace/quotas/{workspace_id}")
def quota(
    workspace_id: str,
    repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return get_workspace_quota(
        workspace_id,
        repository,
    )


@router.post("/workspace/quotas/{workspace_id}")
def update_quota(
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
    return set_workspace_quota(
        workspace_id,
        payload,
        updated_by_user_id=principal.user_id,
        repository=repository,
    )
