from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, BigInteger


class Insight(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    chat_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, index=True)
    )

    message: str

    insight_type: str

    created_at: datetime = Field(default_factory=datetime.utcnow)