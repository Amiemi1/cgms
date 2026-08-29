from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditRecord(SQLModel, table=True):
    """Append-only enterprise audit evidence."""

    __tablename__: ClassVar[str] = (
        "enterprise_audit_record"
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('security', 'domain_event', "
            "'explainability', 'governance')",
            name="ck_enterprise_audit_category",
        ),
        CheckConstraint(
            "TRIM(action) <> ''",
            name="ck_enterprise_audit_action_required",
        ),
        CheckConstraint(
            "TRIM(source) <> ''",
            name="ck_enterprise_audit_source_required",
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    record_id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(
            String(36),
            unique=True,
            index=True,
            nullable=False,
        ),
    )

    origin_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(160),
            unique=True,
            index=True,
            nullable=True,
        ),
    )

    category: str = Field(
        sa_column=Column(
            String(32),
            index=True,
            nullable=False,
        )
    )

    action: str = Field(
        sa_column=Column(
            String(160),
            index=True,
            nullable=False,
        )
    )

    source: str = Field(
        sa_column=Column(
            String(160),
            nullable=False,
        )
    )

    workspace_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(64),
            ForeignKey("workspace.id"),
            index=True,
            nullable=True,
        ),
    )

    actor_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(64),
            index=True,
            nullable=True,
        ),
    )

    subject_type: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(64),
            nullable=True,
        ),
    )

    subject_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(160),
            nullable=True,
        ),
    )

    outcome: str = Field(
        default="recorded",
        sa_column=Column(
            String(32),
            nullable=False,
        ),
    )

    correlation_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(128),
            index=True,
            nullable=True,
        ),
    )

    causation_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(128),
            nullable=True,
        ),
    )

    details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(
            JSON,
            nullable=False,
        ),
    )

    occurred_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            index=True,
            nullable=False,
        ),
    )

    stored_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            index=True,
            nullable=False,
        ),
    )
