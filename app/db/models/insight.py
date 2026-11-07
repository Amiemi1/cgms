from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    String,
)
from sqlmodel import Field, SQLModel


class Insight(SQLModel, table=True):

    __table_args__ = (
        CheckConstraint(
            (
                "NOT ("
                "chat_id IS NOT NULL AND "
                "account_user_id IS NOT NULL"
                ")"
            ),
            name=(
                "ck_insight_identity_scope_at_most_one"
            ),
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    workspace_id: str = Field(
        sa_column=Column(
            String(64),
            index=True,
            nullable=False,
        )
    )

    # Legacy chat identity remains optional because historical
    # Insight semantics permit workspace-level rows.
    chat_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            index=True,
            nullable=True,
        ),
    )

    # Authenticated browser/product account identity.
    account_user_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            ForeignKey("user.id"),
            index=True,
            nullable=True,
        ),
    )

    message: str

    insight_type: str

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
