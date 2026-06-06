from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def find_dependency_chain(session, start_id, max_depth=3):

    visited = set()
    chain = []

    def dfs(memory_id, depth):

        if depth > max_depth:
            return

        if memory_id in visited:
            return

        visited.add(memory_id)

        relations = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == memory_id
            )
        ).all()

        for rel in relations:

            target_id = rel.target_memory_id

            memory = session.get(Memory, target_id)

            if not memory:
                continue

            chain.append({
                "id": memory.id,
                "summary": memory.summary,
                "type": memory.memory_type
            })

            dfs(target_id, depth + 1)

    dfs(start_id, 0)

    return chain