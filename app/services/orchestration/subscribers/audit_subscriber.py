"""
CGMS Audit Event Subscriber

Release:
    v1.75 - Enterprise Event Bus

Purpose:
    Persists canonical domain-event audit evidence.
"""

from __future__ import annotations

from app.services.orchestration.domain_event import DomainEvent
from app.services.persistence.audit_store import (
    get_persistent_audit_store,
)


def audit_subscriber(event: DomainEvent) -> None:
    """
    Persist a canonical audit record for a domain event.
    """
    get_persistent_audit_store().append_domain_event(
        event
    )
