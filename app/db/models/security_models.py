from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(SQLModel, table=True):

    __tablename__: ClassVar[str] = "user_role"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            index=True,
            nullable=False,
        )
    )

    role: str = Field(
        index=True
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
    )


class SecurityLog(SQLModel, table=True):

    __tablename__: ClassVar[str] = "security_log"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            nullable=False,
        )
    )

    workspace_id: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(64),
            index=True,
            nullable=True,
        ),
    )

    action: str

    details: Optional[str] = None

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
    )


class BrowserLoginThrottleRecord(
    SQLModel,
    table=True,
):
    """
    Persistent browser-login throttle state.

    ``throttle_key`` is an HMAC-derived pseudonymous identifier.
    Raw email addresses and network addresses are never stored.
    """

    __tablename__: ClassVar[str] = (
        "browser_login_throttle"
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    throttle_key: str = Field(
        sa_column=Column(
            String(64),
            unique=True,
            index=True,
            nullable=False,
        )
    )

    scope: str = Field(
        sa_column=Column(
            String(16),
            index=True,
            nullable=False,
        )
    )

    failure_count: int = Field(
        default=0,
        sa_column=Column(
            Integer,
            nullable=False,
        ),
    )

    window_started_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        )
    )

    blocked_until: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            index=True,
            nullable=True,
        ),
    )

    last_failure_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        )
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
            index=True,
            nullable=False,
        ),
    )


class BrowserSessionRecord(
    SQLModel,
    table=True,
):

    __tablename__: ClassVar[str] = (
        "browser_session"
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    token_id: str = Field(
        sa_column=Column(
            String(64),
            unique=True,
            index=True,
            nullable=False,
        )
    )

    user_id: int = Field(
        sa_column=Column(
            BigInteger,
            index=True,
            nullable=False,
        )
    )

    workspace_id: str = Field(
        default="default",
        sa_column=Column(
            String(64),
            index=True,
            nullable=False,
        ),
    )

    role: str = Field(
        sa_column=Column(
            String(32),
            nullable=False,
        )
    )

    issued_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        )
    )

    expires_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            index=True,
            nullable=False,
        )
    )

    revoked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            index=True,
            nullable=True,
        ),
    )

    revoked_by_user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            nullable=True,
        ),
    )

    revocation_reason: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(64),
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
