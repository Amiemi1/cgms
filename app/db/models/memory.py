# ==============================================================
# MEMORY MODEL
# ==============================================================

from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from pgvector.sqlalchemy import Vector


class Memory(SQLModel, table=True):

    __tablename__ = "memory"

    __table_args__ = (
        CheckConstraint(
            (
                "(chat_id IS NOT NULL AND "
                "account_user_id IS NULL) OR "
                "(chat_id IS NULL AND "
                "account_user_id IS NOT NULL)"
            ),
            name="ck_memory_identity_scope_exactly_one",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

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

    depends_on: Optional[List[int]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    source_message_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer)
    )

    summary: str = Field(
        sa_column=Column(String, nullable=False)
    )

    memory_type: str = Field(
        sa_column=Column(String, index=True)
    )

    status: Optional[str] = Field(
        default="active",
        sa_column=Column(String)
    )

    # ✅ ADD THIS BLOCK (GOAL LINK)
    goal_id: Optional[int] = Field(default=None, index=True)

    priority: Optional[int] = Field(
        default=50,
        sa_column=Column(Integer)
    )

    # ------------------------------------------------
    # IMPORTANCE SCORE
    # ------------------------------------------------
    importance: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, default=1)
    )

    reminder_time: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime)
    )

    reminder_sent: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )

    # ------------------------------------------------
    # VECTOR EMBEDDING (pgvector)
    # ------------------------------------------------
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(384))
    )

    # ------------------------------------------------
    # MEMORY CLUSTERING SUPPORT
    # ------------------------------------------------
    cluster_count: int = Field(
        default=1,
        sa_column=Column(Integer, nullable=False, default=1)
    )

    # ------------------------------------------------
    # DECISION INTEGRITY (TAMPER PROTECTION)
    # ------------------------------------------------
    decision_hash: Optional[str] = Field(
        default=None,
        index=True
    )

    decision_verified: bool = Field(
        default=True
    )

    # ------------------------------------------------
    # GOVERNANCE LOCK
    # ------------------------------------------------
    is_locked: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, default=False)
    )


# ==============================================================
# AUTO MEMORY GRAPH LINKING
# ==============================================================

from sqlalchemy import event

from app.db.session import SessionLocal
from app.services.memory.memory_graph import link_memories
from app.services.memory.consolidation_engine import consolidate_memory


@event.listens_for(Memory, "after_insert")
def memory_after_insert(mapper, connection, target):

    session = SessionLocal()

    try:

        # ------------------------------------------------
        # CONSOLIDATE DUPLICATES
        # ------------------------------------------------

        memory = consolidate_memory(session, target)

        # ------------------------------------------------
        # BUILD MEMORY GRAPH RELATIONSHIPS
        # ------------------------------------------------

        link_memories(session, memory)

    finally:
        session.close()
