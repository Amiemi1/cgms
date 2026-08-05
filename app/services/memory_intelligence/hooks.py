from app.services.memory_intelligence.events import (
    process_memory_event
)
from app.services.workspace.tenant_scope import normalize_workspace_id


SUPPORTED_MEMORY_EVENTS = [
    "MemoryCreated",
    "MemoryUpdated",
    "MemoryReferenced",
    "MemoryArchived",
]


def handle_memory_intelligence_hook(
    event_name: str,
    memory_id: int,
    workspace_id: str,
):

    if event_name not in SUPPORTED_MEMORY_EVENTS:

        return {
            "processed": False,
            "reason": "unsupported_event",
            "event": event_name,
        }

    return process_memory_event(
        {
            "event": event_name,
            "memory_id": memory_id,
            "workspace_id": normalize_workspace_id(
                workspace_id
            ),
        }
    )
