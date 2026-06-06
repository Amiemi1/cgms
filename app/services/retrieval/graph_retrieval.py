from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def expand_memory_graph(session, memory_ids):

    expanded_memories = []

    for m_id in memory_ids:

        relations = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.target_memory_id == m_id
            )
        ).all()

        for rel in relations:

            memory = session.get(Memory, rel.source_memory_id)

            if memory:
                expanded_memories.append(memory)

    return expanded_memories