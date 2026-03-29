from typing import Optional
from sqlmodel import SQLModel, Field


class MemoryRelationship(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    source_memory_id: int = Field(index=True)

    target_memory_id: int = Field(index=True)

    relationship_type: str = Field(index=True)