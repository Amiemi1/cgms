from typing import Optional, ClassVar
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger, String


class User(SQLModel, table=True):

    __tablename__: ClassVar[str] = "user"

    # Telegram IDs require BIGINT
    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True)
    )

    email: str = Field(
        sa_column=Column(String, unique=True, index=True)
    )

    password_hash: str = Field(
        sa_column=Column(String)
    )

    # Telegram chat id must also be BIGINT
    chat_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, index=True)
    )