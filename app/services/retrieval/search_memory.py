from sqlmodel import select

from app.db.models.memory import Memory
from app.db.session import get_session


def search_memory(chat_id: int, query: str) -> list[Memory]:
    with get_session() as session:
        statement = select(Memory).where(
            Memory.chat_id == chat_id,
            Memory.summary.ilike(f"%{query}%")
        )
        results = session.exec(statement).all()
        return results