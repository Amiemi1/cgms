from typing import List

from sqlmodel import Session, select

from app.db.models.memory import Memory
from app.services.retrieval.embedding_service import generate_embedding


def vector_search(
    session: Session,
    query: str,
    chat_id: int,
    limit: int = 10
) -> List[Memory]:

    embedding = generate_embedding(query)

    if not embedding:
        return []

    statement = (
        select(Memory)
        .where(Memory.chat_id == chat_id)
        .order_by(Memory.embedding.cosine_distance(embedding))
        .limit(limit)
    )

    results = session.exec(statement).all()

    return results