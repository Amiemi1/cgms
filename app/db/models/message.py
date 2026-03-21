from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Column
from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_message_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    chat_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    user_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, nullable=True))
    chat_type: str
    text: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
