from sqlmodel import SQLModel, Field
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    String,
)
from datetime import datetime
from typing import Optional

class Goal(SQLModel, table=True):

    __table_args__ = (
        CheckConstraint(
            (
                "(chat_id IS NOT NULL AND "
                "account_user_id IS NULL) OR "
                "(chat_id IS NULL AND "
                "account_user_id IS NOT NULL)"
            ),
            name="ck_goal_identity_scope_exactly_one",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    name: str
    description: Optional[str] = None

    status: str = "active"

    # Legacy Telegram/chat ingress identity.
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

    created_at: datetime = Field(default_factory=datetime.utcnow)
