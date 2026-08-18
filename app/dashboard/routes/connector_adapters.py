from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.connectors.calendar_adapter import (
    process_calendar_event,
)
from app.services.connectors.gmail_adapter import (
    process_gmail_event,
)
from app.services.connectors.slack_adapter import (
    process_slack_event,
)
from app.services.connectors.teams_adapter import (
    process_teams_event,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
    get_workspace_control_repository,
)


router = APIRouter()


@router.post("/adapters/slack")
def slack_adapter(
    payload: dict,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    quota_repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return process_slack_event(
        payload,
        principal.workspace_id,
        quota_repository,
    )


@router.post("/adapters/teams")
def teams_adapter(
    payload: dict,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    quota_repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return process_teams_event(
        payload,
        principal.workspace_id,
        quota_repository,
    )


@router.post("/adapters/gmail")
def gmail_adapter(
    payload: dict,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    quota_repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return process_gmail_event(
        payload,
        principal.workspace_id,
        quota_repository,
    )


@router.post("/adapters/calendar")
def calendar_adapter(
    payload: dict,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    quota_repository: Annotated[
        WorkspaceControlRepository,
        Depends(get_workspace_control_repository),
    ],
):
    return process_calendar_event(
        payload,
        principal.workspace_id,
        quota_repository,
    )
