from typing import Optional
from datetime import datetime

from sqlmodel import Field, SQLModel
from sqlalchemy import BigInteger, Column


class Learning(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    memory_id: int = Field(sa_column=Column(BigInteger, nullable=False))

    action: str  # completed / delayed / ignored

    created_at: datetime = Field(default_factory=datetime.utcnow)