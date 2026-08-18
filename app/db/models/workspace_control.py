from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlmodel import Field, SQLModel


DEFAULT_MAX_EVENTS = 1000
DEFAULT_MAX_CONNECTORS = 4
DEFAULT_MAX_USERS = 10


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceControl(SQLModel, table=True):
    __tablename__: ClassVar[str] = "workspace_control"

    __table_args__ = (
        CheckConstraint(
            "max_events >= 0",
            name="ck_workspace_control_max_events_nonnegative",
        ),
        CheckConstraint(
            "max_connectors >= 0",
            name="ck_workspace_control_max_connectors_nonnegative",
        ),
        CheckConstraint(
            "max_users >= 0",
            name="ck_workspace_control_max_users_nonnegative",
        ),
    )

    workspace_id: str = Field(
        sa_column=Column(
            String(64),
            ForeignKey(
                "workspace.id",
                ondelete="CASCADE",
            ),
            primary_key=True,
        )
    )

    suspension_reason: str | None = Field(
        default=None,
        sa_column=Column(
            String(500),
            nullable=True,
        ),
    )

    max_events: int = Field(
        default=DEFAULT_MAX_EVENTS,
        sa_column=Column(
            Integer,
            nullable=False,
        ),
    )

    max_connectors: int = Field(
        default=DEFAULT_MAX_CONNECTORS,
        sa_column=Column(
            Integer,
            nullable=False,
        ),
    )

    max_users: int = Field(
        default=DEFAULT_MAX_USERS,
        sa_column=Column(
            Integer,
            nullable=False,
        ),
    )

    updated_by_user_id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey(
                "user.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
    )
