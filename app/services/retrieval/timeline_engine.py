from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def build_memory_timeline(session, memory_ids):

    timeline = []

    for memory_id in memory_ids:

        memory = session.get(Memory, memory_id)

        if not memory:
            continue

        # -----------------------------
        # Find upstream memories
        # -----------------------------

        relations = session.exec(

            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == memory_id
            )

        ).all()

        for r in relations:

            target = session.get(Memory, r.target_memory_id)

            if target:

                timeline.append({
                    "summary": target.summary,
                    "type": target.memory_type
                })

        # -----------------------------
        # Add current memory
        # -----------------------------

        timeline.append({
            "summary": memory.summary,
            "type": memory.memory_type
        })

    # remove duplicates

    seen = set()
    unique = []

    for t in timeline:

        if t["summary"] not in seen:

            seen.add(t["summary"])
            unique.append(t)

    return unique