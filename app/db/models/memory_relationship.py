from typing import Optional
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field


class MemoryRelationship(SQLModel, table=True):

    __tablename__ = "memory_relationship"

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    source_memory_id: int
    target_memory_id: int

    relationship_type: str
