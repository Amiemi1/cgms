"""
CGMS Enterprise Event Bus Bootstrap

Release:
    v1.75 - Enterprise Event Bus

Purpose:
    Registers default platform subscribers.
"""

from __future__ import annotations

from app.services.memory_intelligence.subscribers import (
    memory_intelligence_subscriber,
)
from app.services.orchestration.contracts.memory_events import MemoryEventName
from app.services.orchestration.event_registry import DEFAULT_EVENT_REGISTRY

from app.services.orchestration.subscribers.audit_subscriber import (
    audit_subscriber,
)

_BOOTSTRAPPED = False


def bootstrap_event_bus() -> None:
    """
    Register default Event Bus subscribers.

    This function is idempotent and safe to call multiple times.
    """

    global _BOOTSTRAPPED

    if _BOOTSTRAPPED:
        return

    DEFAULT_EVENT_REGISTRY.subscribe(
        MemoryEventName.CREATED,
        memory_intelligence_subscriber,
    )

    DEFAULT_EVENT_REGISTRY.subscribe(
        MemoryEventName.UPDATED,
        memory_intelligence_subscriber,
    )

    DEFAULT_EVENT_REGISTRY.subscribe(
        MemoryEventName.REOPENED,
        memory_intelligence_subscriber,
    )

    DEFAULT_EVENT_REGISTRY.subscribe(
        MemoryEventName.RESTORED,
        memory_intelligence_subscriber,
    )

    DEFAULT_EVENT_REGISTRY.subscribe(
        MemoryEventName.PRIORITY_CHANGED,
        memory_intelligence_subscriber,
    )
    for event_name in MemoryEventName:
        DEFAULT_EVENT_REGISTRY.subscribe(
            event_name,
            audit_subscriber,
        )
    _BOOTSTRAPPED = True