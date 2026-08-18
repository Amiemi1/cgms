import asyncio
import inspect
from datetime import datetime, timezone

from app.services.orchestration.event_router import route_memory_update
from app.services.workspace.quotas import get_workspace_quota
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
)
from app.services.workspace.tenant_scope import (
    normalize_workspace_id,
)


INGESTED_EVENTS = []


def _run_orchestration(result) -> None:
    """
    Execute sync or async orchestration result safely from sync ingestion.

    TODO(v1.76):
    Convert connector ingestion to async and await orchestration directly.
    """

    if not inspect.isawaitable(result):
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(result)
        return

    loop.create_task(result)


def ingest_external_event(
    source: str,
    payload: dict,
    workspace_id: str,
    quota_repository: WorkspaceControlRepository | None = None,
):
    resolved_workspace_id = normalize_workspace_id(
        workspace_id
    )
    record = {
        "workspace": resolved_workspace_id,
        "source": source,
        "payload": payload,
        "status": "received",
        "receivedAt": datetime.now(timezone.utc).isoformat(),
    }

    quota = enforce_event_quota(
        resolved_workspace_id,
        quota_repository,
    )

    if not quota["allowed"]:
        record["status"] = "blocked"
        record["quota"] = quota
        return record

    INGESTED_EVENTS.insert(0, record)
    del INGESTED_EVENTS[300:]

    try:
        result = route_memory_update(
            {
                "source": source,
                "external": True,
                "payload": payload,
                "workspace_id": resolved_workspace_id,
            }
        )

        _run_orchestration(result)

        record["orchestrated"] = True

    except Exception as e:
        record["orchestrated"] = False
        record["error"] = str(e)

    print("📥 EXTERNAL EVENT INGESTED", record)

    return record


def get_ingested_events(
    workspace_id: str,
    limit: int = 100,
):
    resolved_workspace_id = normalize_workspace_id(
        workspace_id
    )
    return [
        event
        for event in INGESTED_EVENTS
        if event.get("workspace")
        == resolved_workspace_id
    ][:limit]


def enforce_event_quota(
    workspace_id: str,
    quota_repository: WorkspaceControlRepository | None = None,
):
    resolved_workspace_id = normalize_workspace_id(
        workspace_id
    )
    quota = get_workspace_quota(
        resolved_workspace_id,
        quota_repository,
    )

    count = len(
        [
            event
            for event in INGESTED_EVENTS
            if event.get("workspace")
            == resolved_workspace_id
        ]
    )

    return {
        "allowed": count < quota["maxEvents"],
        "usage": count,
        "limit": quota["maxEvents"],
    }
