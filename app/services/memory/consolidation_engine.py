from sqlmodel import select
from app.db.models.memory import Memory


def consolidate_memory(session, new_memory):

    """
    Consolidate duplicate memories by increasing cluster_count
    instead of deleting records during flush cycle.
    """

    existing = session.exec(
        select(Memory).where(
            Memory.chat_id == new_memory.chat_id,
            Memory.summary == new_memory.summary,
            Memory.id != new_memory.id
        )
    ).first()

    if existing:

        # Increase cluster count
        existing.cluster_count += 1

        session.add(existing)
        session.commit()

        print("MEMORY MERGED:", existing.summary)

        return existing

    return new_memory