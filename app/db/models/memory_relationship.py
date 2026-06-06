from typing import Optional
from sqlmodel import SQLModel, Field


class MemoryRelationship(SQLModel, table=True):

    __tablename__ = "memory_relationship"

    id: Optional[int] = Field(default=None, primary_key=True)

    source_memory_id: int
    target_memory_id: int

    relationship_type: str