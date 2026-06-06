# ==============================================================
# SYSTEM INTELLIGENCE ENGINE
# ==============================================================

from collections import Counter
from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def generate_intelligence_report(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    memory_count = len(memories)

    tasks = [m for m in memories if m.memory_type == "task"]
    events = [m for m in memories if m.memory_type == "event"]
    decisions = [m for m in memories if m.memory_type == "decision"]

    relationship_count = len(relationships)

    response = "🧠 CGMS Intelligence Report\n\n"

    response += f"Memories stored: {memory_count}\n"
    response += f"Tasks: {len(tasks)}\n"
    response += f"Events: {len(events)}\n"
    response += f"Decisions: {len(decisions)}\n"
    response += f"Relationships: {relationship_count}\n\n"

    # ------------------------------------------------
    # TOPIC DETECTION
    # ------------------------------------------------

    words = []

    for m in memories:

        tokens = m.summary.lower().split()

        for t in tokens:

            if len(t) > 4:
                words.append(t)

    common = Counter(words).most_common(3)

    if common:

        response += "🔥 Current Focus:\n\n"

        for word, count in common:
            response += f"• {word} related work\n"

    return response