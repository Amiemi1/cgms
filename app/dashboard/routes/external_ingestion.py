from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.connectors.event_ingestion import (
    get_ingested_events,
    ingest_external_event,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
    get_workspace_control_repository,
)


router = APIRouter()


@router.post("/ingest/{source}")
def ingest(
    source: str,
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
    return {
        "ok": True,
        "event": ingest_external_event(
            source,
            payload,
            principal.workspace_id,
            quota_repository,
        ),
    }


@router.get("/ingest/events")
def events(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(enforce_application_authorization),
    ],
    limit: int = 100,
):
    return {
        "events": get_ingested_events(
            principal.workspace_id,
            limit,
        )
    }
