from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(SQLModel, table=True):
    __tablename__: ClassVar[str] = "workspace"

    id: str = Field(
        sa_column=Column(
            String(64),
            primary_key=True,
        )
    )

    name: str = Field(
        sa_column=Column(
            String(160),
            nullable=False,
        )
    )

    status: str = Field(
        default="active",
        sa_column=Column(
            String(16),
            nullable=False,
            index=True,
        ),
    )

    created_by_user_id: int | None = Field(
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


class WorkspaceMembership(SQLModel, table=True):
    __tablename__: ClassVar[str] = "workspace_membership"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name=(
                "uq_workspace_membership_"
                "workspace_user"
            ),
        ),
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    workspace_id: str = Field(
        sa_column=Column(
            String(64),
            ForeignKey(
                "workspace.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )

    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey(
                "user.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )

    status: str = Field(
        default="active",
        sa_column=Column(
            String(16),
            nullable=False,
            index=True,
        ),
    )

    is_default: bool = Field(
        default=False,
        sa_column=Column(
            Boolean,
            nullable=False,
            index=True,
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
