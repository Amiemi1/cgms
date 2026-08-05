from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class MemoryScore(SQLModel, table=True):

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    memory_id: int = Field(
        index=True
    )

    importance: int

    confidence: int

    freshness: int

    priority: int

    composite: int

    factors_json: str

    version: str = "v1.74"

    last_calculated: datetime = Field(
        default_factory=datetime.utcnow
    )
