"""
CGMS Audit Event Subscriber

Release:
    v1.75 - Enterprise Event Bus

Purpose:
    Provides the first audit subscriber stub for Event Bus integration.
"""

from __future__ import annotations

from app.services.orchestration.domain_event import DomainEvent


AUDIT_EVENT_LOG: list[dict] = []


def audit_subscriber(event: DomainEvent) -> None:
    """
    Capture a minimal audit record for a domain event.

    This is an in-memory stub for v1.75.

    TODO(v1.76):
    Replace this with persistent audit storage.
    """

    AUDIT_EVENT_LOG.append(
        {
            "event_id": event.event_id,
            "event_name": event.event_name,
            "event_version": event.event_version,
            "source": event.source,
            "workspace_id": event.workspace_id,
            "actor_id": event.actor_id,
            "correlation_id": event.correlation_id,
            "payload": event.payload,
            "occurred_at": event.occurred_at.isoformat(),
        }
    )


def clear_audit_event_log() -> None:
    """
    Clear the in-memory audit event log.

    Intended for tests.
    """

    AUDIT_EVENT_LOG.clear()