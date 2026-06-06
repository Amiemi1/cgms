from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship

from app.services.retrieval.vector_search import search_similar_memories


SIMILARITY_THRESHOLD = 0.70


def create_vector_relationships(memory):

    session = SessionLocal()

    try:

        results = search_similar_memories(memory.summary)

        for result in results:

            if result["id"] == memory.id:
                continue

            if result["score"] < SIMILARITY_THRESHOLD:
                continue

            relationship = MemoryRelationship(
                source_memory_id=memory.id,
                target_memory_id=result["id"],
                relationship_type="semantic"
            )

            session.add(relationship)

        session.commit()

    finally:

        session.close()