from __future__ import annotations

from typing import Any

from app.services.persistence.audit_store import (
    EXPLAINABILITY_AUDIT,
    PersistentAuditStore,
    audit_record_payload,
    get_persistent_audit_store,
)


def store_audit_record(
    record: dict[str, Any],
    *,
    workspace_id: str | None = None,
    actor_id: str | None = None,
    correlation_id: str | None = None,
    audit_store: PersistentAuditStore | None = None,
) -> dict[str, Any]:
    """Persist explanation evidence through the enterprise audit store."""
    resolved_store = (
        audit_store
        or get_persistent_audit_store()
    )
    event_name = record.get(
        "event"
    )
    persisted = resolved_store.append(
        category=EXPLAINABILITY_AUDIT,
        action="explanation.generated",
        source="explainability_engine",
        workspace_id=workspace_id,
        actor_id=actor_id,
        subject_type="runtime_event",
        subject_id=(
            str(event_name)
            if event_name is not None
            else None
        ),
        outcome="generated",
        correlation_id=correlation_id,
        details=record,
    )

    return audit_record_payload(
        persisted
    )


def get_audit_records(
    *,
    workspace_id: str,
    limit: int = 50,
    include_global: bool = False,
    audit_store: PersistentAuditStore | None = None,
) -> list[dict[str, Any]]:
    """Read only the authenticated workspace's audit evidence."""
    resolved_store = (
        audit_store
        or get_persistent_audit_store()
    )

    return [
        audit_record_payload(record)
        for record in resolved_store.list_for_workspace(
            workspace_id,
            limit=limit,
            include_global=include_global,
        )
    ]
