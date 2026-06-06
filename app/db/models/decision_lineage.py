from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, BigInteger


# ==============================================================
# DECISION LINEAGE MODEL
# ==============================================================

class DecisionLineage(SQLModel, table=True):

    __tablename__ = "decision_lineage"

    id: Optional[int] = Field(default=None, primary_key=True)

    decision_id: int = Field(index=True)

    source_memory_id: Optional[int] = Field(default=None)

    reasoning_engine: Optional[str] = Field(default=None)

    triggered_by_user: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)