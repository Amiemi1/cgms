from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def get_memory_timeline(session, chat_id: int):

    memories = session.exec(
        select(Memory)
        .where(Memory.chat_id == chat_id)
        .order_by(Memory.created_at.asc())
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    timeline = []

    for memory in memories:

        node = {
            "id": memory.id,
            "type": memory.memory_type,
            "summary": memory.summary,
            "created_at": memory.created_at,
            "links": []
        }

        for rel in relationships:

            if rel.source_memory_id == memory.id:

                node["links"].append({
                    "target": rel.target_memory_id,
                    "type": rel.relationship_type
                })

        timeline.append(node)

    return timeline