# ==============================================================
# BRAIN STATUS ENGINE
# ==============================================================

from sqlmodel import select
from collections import Counter

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def get_brain_status(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    memory_count = len(memories)
    relationship_count = len(relationships)

    types = Counter([m.memory_type for m in memories])

    task_count = types.get("task", 0)
    decision_count = types.get("decision", 0)
    event_count = types.get("event", 0)

    blocked_tasks = [
        m for m in memories
        if m.memory_type == "task" and m.priority and m.priority < 30
    ]

    reasoning_chains = relationship_count

    response = "🧠 CGMS Cognitive Status\n\n"

    response += f"Memories stored: {memory_count}\n"
    response += f"Graph relationships: {relationship_count}\n\n"

    response += f"Tasks: {task_count}\n"
    response += f"Decisions: {decision_count}\n"
    response += f"Events: {event_count}\n\n"

    response += f"Blocked tasks: {len(blocked_tasks)}\n"
    response += f"Active reasoning chains: {reasoning_chains}\n"

    return response