from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Column, BigInteger


class User(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)

    email: str = Field(index=True, unique=True)

    password_hash: str

    # Telegram chat id must be BIGINT
    chat_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger)
    )