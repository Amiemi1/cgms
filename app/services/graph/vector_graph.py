from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship

from app.services.retrieval.vector_search import search_similar_memories
from app.services.workspace.tenant_scope import (
    inherit_workspace_id,
    load_scoped_record,
)


SIMILARITY_THRESHOLD = 0.70


def create_vector_relationships(memory):

    session = SessionLocal()

    try:
        workspace_id = inherit_workspace_id(memory)
        results = search_similar_memories(memory.summary)

        for result in results:

            if result["id"] == memory.id:
                continue

            if result["score"] < SIMILARITY_THRESHOLD:
                continue

            target = load_scoped_record(
                session,
                Memory,
                result["id"],
                workspace_id,
            )

            if target is None:
                continue

            relationship = MemoryRelationship(
                workspace_id=workspace_id,
                source_memory_id=memory.id,
                target_memory_id=target.id,
                relationship_type="semantic"
            )

            session.add(relationship)

        session.commit()

    finally:

        session.close()
