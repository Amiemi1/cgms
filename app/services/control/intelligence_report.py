
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
    decisions = [m for m in memories if m.memory_type == "decision"]
    events = [m for m in memories if m.memory_type == "event"]

    relationship_count = len(relationships)

    # -------------------------
    # Focus detection
    # -------------------------

    words = []

    for m in memories:

        tokens = m.summary.lower().split()

        for token in tokens:

            if len(token) > 4:
                words.append(token)

    focus = Counter(words).most_common(1)

    focus_topic = focus[0][0] if focus else "none"

    report = "🧠 CGMS Intelligence Report\n\n"

    report += f"Memories stored: {memory_count}\n"
    report += f"Tasks: {len(tasks)}\n"
    report += f"Decisions: {len(decisions)}\n"
    report += f"Events: {len(events)}\n"
    report += f"Graph relationships: {relationship_count}\n\n"

    report += f"Top focus area: {focus_topic}\n"

    if len(tasks) > len(decisions):

        report += "⚠ Tasks exceed decisions — approvals may be pending\n"

    report += "\nSystem cognitive status: operational"

    return report