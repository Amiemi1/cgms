from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger


class CandidateMemory(SQLModel, table=True):
    __tablename__ = "candidate_memory"

    id: Optional[int] = Field(default=None, primary_key=True)

    chat_id: int = Field(
        sa_column=Column(BigInteger, index=True)
    )

    message_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger)   # 🔥 THIS IS CRITICAL
    )

    memory_type: str
    summary: str
    original_text: Optional[str] = None

    status: str = Field(default="pending")