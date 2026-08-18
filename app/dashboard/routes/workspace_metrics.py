from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.workspace.metrics import (
    workspace_metrics,
)
from app.services.workspace.repository import (
    WorkspaceRepository,
    get_workspace_repository,
)


router = APIRouter()


@router.get("/workspace/metrics")
def metrics(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    repository: Annotated[
        WorkspaceRepository,
        Depends(get_workspace_repository),
    ],
):
    return workspace_metrics(
        principal.workspace_id,
        repository=repository,
    )
