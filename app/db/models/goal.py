from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger, String
from datetime import datetime
from typing import Optional

class Goal(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    name: str
    description: Optional[str] = None

    status: str = "active"

    chat_id: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
