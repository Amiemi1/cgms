from app.services.memory_intelligence.events import (
    process_memory_event
)


SUPPORTED_MEMORY_EVENTS = [
    "MemoryCreated",
    "MemoryUpdated",
    "MemoryReferenced",
    "MemoryArchived",
]


def handle_memory_intelligence_hook(
    event_name: str,
    memory_id: int
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
        }
    )