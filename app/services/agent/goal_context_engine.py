# =====================================================
# GOAL CONTEXT ENGINE
# Expands goal understanding using memory graph
# =====================================================

from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def build_goal_context(session, chat_id: int, goal: str):

    goal = goal.lower()

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    related = []

    # --------------------------------
    # Step 1 — keyword matching
    # --------------------------------

    for m in memories:

        if any(word in m.summary.lower() for word in goal.split()):

            related.append(m)

    if not related:
        return []

    # --------------------------------
    # Step 2 — expand via graph
    # --------------------------------

    context = set(related)

    for m in related:

        relationships = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.source_memory_id == m.id
            )
        ).all()

        for r in relationships:

            linked = session.get(Memory, r.target_memory_id)

            if linked:
                context.add(linked)

    return list(context)