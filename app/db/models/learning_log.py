# ==============================================================
# LEARNING LOG MODEL
# ==============================================================

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class LearningLog(SQLModel, table=True):

    __tablename__ = "learning_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    action: str
    context: str
    result: str

    created_at: datetime = Field(default_factory=datetime.utcnow)