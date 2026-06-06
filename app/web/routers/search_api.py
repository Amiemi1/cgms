from fastapi import APIRouter

from app.db.session import SessionLocal
from app.services.embedding.embedding_service import generate_embedding
from app.services.search.vector_search_service import search_memories

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get("/")
def search(query: str, chat_id: int):

    session = SessionLocal()

    try:

        embedding = generate_embedding(query)

        results = search_memories(
            session=session,
            chat_id=chat_id,
            embedding=embedding,
            limit=5
        )

        return [
            {
                "id": r.id,
                "summary": r.summary,
                "type": r.memory_type
            }
            for r in results
        ]

    finally:
        session.close()