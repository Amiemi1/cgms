from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger, Integer, String, DateTime


class CandidateMemory(SQLModel, table=True):

    __tablename__ = "candidate_memory"

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    # Telegram chat IDs must be BIGINT
    chat_id: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False)
    )

    message_id: Optional[int] = Field(
        default=None,
        sa_column=Column(Integer)
    )

    summary: str = Field(
        sa_column=Column(String, nullable=False)
    )

    memory_type: str = Field(
        sa_column=Column(String, index=True)
    )

    status: str = Field(
        default="pending",
        sa_column=Column(String, nullable=False, index=True)
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False)
    )
