from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger
from datetime import datetime
from typing import Optional

class Goal(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    description: Optional[str] = None

    status: str = "active"

    chat_id: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)