from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger
from typing import Optional
from datetime import datetime


class MemoryAccess(SQLModel, table=True):

    __tablename__ = "memory_access"

    id: Optional[int] = Field(default=None, primary_key=True)

    memory_id: int = Field(index=True)

    user_id: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False)
    )

    permission: str = Field(index=True)  # read, write, admin

    created_at: datetime = Field(default_factory=datetime.utcnow)