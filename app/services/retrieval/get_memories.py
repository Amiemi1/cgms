from sqlmodel import select

from app.db.models.memory import Memory
from app.db.session import get_session


def get_memories(chat_id: int) -> list[Memory]:
    with get_session() as session:
        statement = select(Memory).where(Memory.chat_id == chat_id)
        results = session.exec(statement).all()
        return results