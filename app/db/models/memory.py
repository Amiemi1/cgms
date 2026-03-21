from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger
from pgvector.sqlalchemy import Vector


class Memory(SQLModel, table=True):
    __tablename__ = "memory"

    # =========================
    # PRIMARY KEY
    # =========================
    id: Optional[int] = Field(default=None, primary_key=True)

    # =========================
    # CONTEXT (FIXED → BIGINT)
    # =========================
    chat_id: int = Field(
        sa_column=Column(BigInteger, index=True)
    )

    source_message_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger)
    )

    # =========================
    # MEMORY CONTENT
    # =========================
    memory_type: str = Field(index=True)
    summary: str

    # =========================
    # STATE
    # =========================
    status: str = Field(default="active")
    priority: int = Field(default=50, index=True)

    # =========================
    # TIME
    # =========================
    reminder_time: Optional[datetime] = Field(default=None, index=True)
    reminder_sent: bool = Field(default=False)

    # =========================
    # VECTOR
    # =========================
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(384))
    )

    # =========================
    # META
    # =========================
    created_at: datetime = Field(default_factory=datetime.utcnow)