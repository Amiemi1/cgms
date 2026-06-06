from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def find_dependent_tasks(session, decision_id):

    relations = session.exec(

        select(MemoryRelationship).where(
            MemoryRelationship.source_memory_id == decision_id
        )

    ).all()

    tasks = []

    for r in relations:

        if r.relationship_type != "resolves":
            continue

        memory = session.get(Memory, r.target_memory_id)

        if memory and memory.memory_type == "task":
            tasks.append(memory.summary)

    return tasks