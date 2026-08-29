from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from sqlmodel import Session, select

from app.db.models.audit_record import AuditRecord
from app.db.session import SessionLocal
from app.services.workspace.repository import (
    InvalidWorkspaceIdentifierError,
    normalize_workspace_identifier,
)


SECURITY_AUDIT = "security"
DOMAIN_EVENT_AUDIT = "domain_event"
EXPLAINABILITY_AUDIT = "explainability"
GOVERNANCE_AUDIT = "governance"

AUDIT_CATEGORIES = frozenset(
    {
        SECURITY_AUDIT,
        DOMAIN_EVENT_AUDIT,
        EXPLAINABILITY_AUDIT,
        GOVERNANCE_AUDIT,
    }
)


class AuditStoreError(RuntimeError):
    """Base error for persistent audit operations."""


class AuditValidationError(AuditStoreError):
    """Raised when audit evidence violates the canonical contract."""


class AuditPersistenceError(AuditStoreError):
    """Raised when audit evidence cannot be persisted or read."""


def _required_text(
    value: object,
    *,
    field_name: str,
    maximum: int,
) -> str:
    if not isinstance(value, str):
        raise AuditValidationError(
            f"Audit {field_name} must be a string."
        )

    normalized = value.strip()

    if not normalized or len(normalized) > maximum:
        raise AuditValidationError(
            f"Audit {field_name} must contain 1 to "
            f"{maximum} characters."
        )

    return normalized


def _optional_text(
    value: object | None,
    *,
    field_name: str,
    maximum: int,
) -> str | None:
    if value is None:
        return None

    return _required_text(
        value,
        field_name=field_name,
        maximum=maximum,
    )


def _workspace_id(
    value: object | None,
) -> str | None:
    if value is None:
        return None

    try:
        return normalize_workspace_identifier(
            value
        )
    except InvalidWorkspaceIdentifierError as exc:
        raise AuditValidationError(
            "Audit workspace identifier is invalid."
        ) from exc


def _occurred_at(
    value: datetime | None,
) -> datetime:
    resolved = value or datetime.now(timezone.utc)

    if not isinstance(resolved, datetime):
        raise AuditValidationError(
            "Audit occurrence time is invalid."
        )

    if resolved.tzinfo is None:
        return resolved.replace(
            tzinfo=timezone.utc
        )

    return resolved.astimezone(
        timezone.utc
    )


def _details(
    value: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise AuditValidationError(
            "Audit details must be an object."
        )

    try:
        serialized = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
        )
        normalized = json.loads(
            serialized
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise AuditValidationError(
            "Audit details must be JSON serializable."
        ) from exc

    return dict(normalized)


def add_audit_record(
    session: Session,
    *,
    category: str,
    action: str,
    source: str,
    workspace_id: object | None = None,
    actor_id: object | None = None,
    subject_type: object | None = None,
    subject_id: object | None = None,
    outcome: str = "recorded",
    correlation_id: object | None = None,
    causation_id: object | None = None,
    details: Mapping[str, Any] | None = None,
    occurred_at: datetime | None = None,
    origin_id: object | None = None,
) -> AuditRecord:
    """
    Add canonical audit evidence to an existing transaction.

    The caller owns commit and rollback so business state and its audit
    evidence can be persisted atomically.
    """
    normalized_category = _required_text(
        category,
        field_name="category",
        maximum=32,
    )

    if normalized_category not in AUDIT_CATEGORIES:
        raise AuditValidationError(
            "Audit category is not supported."
        )

    normalized_origin_id = _optional_text(
        origin_id,
        field_name="origin identifier",
        maximum=160,
    )

    if normalized_origin_id is not None:
        existing = session.exec(
            select(AuditRecord).where(
                AuditRecord.origin_id
                == normalized_origin_id
            )
        ).first()

        if existing is not None:
            return existing

    record = AuditRecord(
        origin_id=normalized_origin_id,
        category=normalized_category,
        action=_required_text(
            action,
            field_name="action",
            maximum=160,
        ),
        source=_required_text(
            source,
            field_name="source",
            maximum=160,
        ),
        workspace_id=_workspace_id(
            workspace_id
        ),
        actor_id=_optional_text(
            str(actor_id)
            if actor_id is not None
            else None,
            field_name="actor identifier",
            maximum=64,
        ),
        subject_type=_optional_text(
            subject_type,
            field_name="subject type",
            maximum=64,
        ),
        subject_id=_optional_text(
            str(subject_id)
            if subject_id is not None
            else None,
            field_name="subject identifier",
            maximum=160,
        ),
        outcome=_required_text(
            outcome,
            field_name="outcome",
            maximum=32,
        ),
        correlation_id=_optional_text(
            correlation_id,
            field_name="correlation identifier",
            maximum=128,
        ),
        causation_id=_optional_text(
            causation_id,
            field_name="causation identifier",
            maximum=128,
        ),
        details=_details(
            details
        ),
        occurred_at=_occurred_at(
            occurred_at
        ),
        stored_at=datetime.now(
            timezone.utc
        ),
    )

    session.add(
        record
    )

    return record


def audit_record_payload(
    record: AuditRecord,
) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "origin_id": record.origin_id,
        "category": record.category,
        "action": record.action,
        "source": record.source,
        "workspace_id": record.workspace_id,
        "actor_id": record.actor_id,
        "subject_type": record.subject_type,
        "subject_id": record.subject_id,
        "outcome": record.outcome,
        "correlation_id": record.correlation_id,
        "causation_id": record.causation_id,
        "details": record.details,
        "occurred_at": record.occurred_at.isoformat(),
        "stored_at": record.stored_at.isoformat(),
    }


class PersistentAuditStore:
    """Workspace-safe persistent authority for enterprise audit evidence."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def append(
        self,
        **values: Any,
    ) -> AuditRecord:
        session = self._session_factory()

        try:
            record = add_audit_record(
                session,
                **values,
            )
            session.commit()
            session.refresh(
                record
            )
            session.expunge(
                record
            )
            return record

        except AuditStoreError:
            session.rollback()
            raise

        except SQLAlchemyError as exc:
            session.rollback()
            raise AuditPersistenceError(
                "Audit evidence could not be persisted."
            ) from exc

        finally:
            session.close()

    def append_domain_event(
        self,
        event: Any,
    ) -> AuditRecord:
        return self.append(
            category=DOMAIN_EVENT_AUDIT,
            action=event.event_name,
            source=event.source,
            workspace_id=event.workspace_id,
            actor_id=event.actor_id,
            subject_type=event.bounded_context,
            subject_id=event.payload.get(
                f"{event.bounded_context}_id"
            ),
            outcome="published",
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            details={
                "event_id": event.event_id,
                "event_version": event.event_version,
                "metadata": event.metadata,
                "payload": event.payload,
            },
            occurred_at=event.occurred_at,
            origin_id=f"domain_event:{event.event_id}",
        )

    def list_for_workspace(
        self,
        workspace_id: object,
        *,
        limit: int = 50,
        include_global: bool = False,
    ) -> tuple[AuditRecord, ...]:
        normalized_workspace_id = _workspace_id(
            workspace_id
        )

        if normalized_workspace_id is None:
            raise AuditValidationError(
                "A workspace identifier is required."
            )

        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
            or limit > 100
        ):
            raise AuditValidationError(
                "Audit read limit must be between 1 and 100."
            )

        session = self._session_factory()

        try:
            scope = (
                or_(
                    AuditRecord.workspace_id
                    == normalized_workspace_id,
                    AuditRecord.workspace_id.is_(
                        None
                    ),
                )
                if include_global
                else (
                    AuditRecord.workspace_id
                    == normalized_workspace_id
                )
            )
            records = session.exec(
                select(AuditRecord).where(
                    scope
                ).order_by(
                    AuditRecord.occurred_at.desc(),
                    AuditRecord.id.desc(),
                ).limit(
                    limit
                )
            ).all()

            for record in records:
                session.expunge(
                    record
                )

            return tuple(records)

        except AuditStoreError:
            raise

        except SQLAlchemyError as exc:
            raise AuditPersistenceError(
                "Audit evidence could not be read."
            ) from exc

        finally:
            session.close()


def get_persistent_audit_store(
) -> PersistentAuditStore:
    return PersistentAuditStore()
