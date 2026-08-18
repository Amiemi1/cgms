from __future__ import annotations

from collections.abc import Sequence

from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS,
)
from app.services.workspace.registry import (
    get_workspaces,
)
from app.services.workspace.repository import (
    WorkspaceRepository,
    get_workspace_repository,
)


def workspace_metrics(
    workspace_id: str | None = None,
    *,
    repository: WorkspaceRepository | None = None,
    events: Sequence[dict[str, object]] | None = None,
) -> dict[str, dict[str, int]]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_repository()
    )
    resolved_events = (
        events
        if events is not None
        else INGESTED_EVENTS
    )

    if workspace_id is None:
        workspace_ids = tuple(
            get_workspaces(
                resolved_repository
            )
        )
    else:
        workspace = resolved_repository.require_workspace(
            workspace_id,
            require_active=True,
        )
        workspace_ids = (workspace.id,)

    result: dict[str, dict[str, int]] = {}

    for resolved_workspace_id in workspace_ids:
        workspace_events = [
            event
            for event in resolved_events
            if event.get("workspace")
            == resolved_workspace_id
        ]
        result[resolved_workspace_id] = {
            "events": len(workspace_events),
            "orchestrated": len(
                [
                    event
                    for event in workspace_events
                    if event.get("orchestrated")
                ]
            ),
            "health": (
                100
                if workspace_events
                else 95
            ),
        }

    return result
