"""
CGMS Memory Intelligence Event Subscribers

Release:
    v1.75 - Enterprise Event Bus
"""

from __future__ import annotations

from app.services.memory_intelligence.events import process_memory_event
from app.services.orchestration.contracts.memory_events import MemoryEventName
from app.services.orchestration.domain_event import DomainEvent


SUPPORTED_EVENT_MAP = {
    MemoryEventName.CREATED: "MemoryCreated",
    MemoryEventName.UPDATED: "MemoryUpdated",
    MemoryEventName.REOPENED: "MemoryReferenced",
    MemoryEventName.RESTORED: "MemoryUpdated",
    MemoryEventName.PRIORITY_CHANGED: "MemoryUpdated",
}


def memory_intelligence_subscriber(event: DomainEvent) -> None:
    """
    Event Bus subscriber for Memory Intelligence recalculation.

    Converts canonical v1.75 DomainEvent objects into the existing
    v1.74 memory-intelligence event format.
    """

    mapped_event_name = SUPPORTED_EVENT_MAP.get(event.event_name)

    if mapped_event_name is None:
        return

    memory_id = event.payload.get("memory_id")
    event_payload = {
        "event": mapped_event_name,
        "memory_id": memory_id,
    }

    if event.workspace_id is not None:
        event_payload["workspace_id"] = event.workspace_id

    process_memory_event(event_payload)
