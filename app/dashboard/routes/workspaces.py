from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.workspace.registry import (
    create_workspace,
    get_workspaces,
)
from app.services.workspace.repository import (
    WorkspaceRepository,
    get_workspace_repository,
)


router = APIRouter()


@router.get("/workspaces")
def workspaces(
    repository: Annotated[
        WorkspaceRepository,
        Depends(get_workspace_repository),
    ],
):
    return get_workspaces(repository)


@router.post("/workspaces")
def create(
    payload: dict[str, object],
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    repository: Annotated[
        WorkspaceRepository,
        Depends(get_workspace_repository),
    ],
):
    return create_workspace(
        str(payload.get("id") or ""),
        payload,
        created_by_user_id=principal.user_id,
        repository=repository,
    )
