from sqlmodel import SQLModel, Field
from sqlalchemy import Column, BigInteger
from typing import Optional, ClassVar
from datetime import datetime


class UserRole(SQLModel, table=True):

    __tablename__: ClassVar[str] = "user_role"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(
        sa_column=Column(BigInteger, index=True, nullable=False)
    )

    role: str = Field(index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SecurityLog(SQLModel, table=True):

    __tablename__: ClassVar[str] = "security_log"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(
        sa_column=Column(BigInteger, nullable=False)
    )

    action: str

    details: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)