"""
CGMS Memory Event Contracts

Release:
    v1.75 - Enterprise Event Bus
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from app.services.orchestration.domain_event import DomainEvent


class MemoryEventName(StrEnum):
    CREATED = "memory.created"
    UPDATED = "memory.updated"
    DELETED = "memory.deleted"
    COMPLETED = "memory.completed"
    REOPENED = "memory.reopened"
    DELAYED = "memory.delayed"
    RESTORED = "memory.restored"
    PRIORITY_CHANGED = "memory.priority_changed"


def memory_created_event(
    *,
    memory_id: str | int,
    source: str,
    workspace_id: str | None = None,
    actor_id: str | None = None,
    memory_type: str | None = None,
    priority: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_name=MemoryEventName.CREATED,
        source=source,
        workspace_id=workspace_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload={
            "memory_id": memory_id,
            "memory_type": memory_type,
            "priority": priority,
        },
        metadata=metadata or {},
    )


def memory_updated_event(
    *,
    memory_id: str | int,
    source: str,
    changed_fields: list[str],
    workspace_id: str | None = None,
    actor_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_name=MemoryEventName.UPDATED,
        source=source,
        workspace_id=workspace_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload={
            "memory_id": memory_id,
            "changed_fields": changed_fields,
        },
        metadata=metadata or {},
    )


def memory_priority_changed_event(
    *,
    memory_id: str | int,
    source: str,
    old_priority: str | int | None,
    new_priority: str | int | None,
    workspace_id: str | None = None,
    actor_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_name=MemoryEventName.PRIORITY_CHANGED,
        source=source,
        workspace_id=workspace_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        payload={
            "memory_id": memory_id,
            "old_priority": old_priority,
            "new_priority": new_priority,
        },
        metadata=metadata or {},
    )