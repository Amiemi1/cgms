# ==============================================================
# LEARNING LOG MODEL
# ==============================================================

from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String
from sqlmodel import SQLModel, Field


class LearningLog(SQLModel, table=True):

    __tablename__ = "learning_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    workspace_id: str = Field(
        sa_column=Column(String(64), index=True, nullable=False)
    )

    action: str
    context: str
    result: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
