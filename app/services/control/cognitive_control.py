from collections import Counter
from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def evaluate_system_state(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    memory_map = {m.id: m for m in memories}

    blocked_tasks = []
    urgent_events = []
    decision_dependencies = []

    # -----------------------------
    # Detect blocked tasks
    # -----------------------------

    for rel in relationships:

        if rel.relationship_type == "resolves":

            decision = memory_map.get(rel.source_memory_id)
            task = memory_map.get(rel.target_memory_id)

            if decision and task:

                blocked_tasks.append(task.summary)

                decision_dependencies.append(
                    f"{decision.summary} → {task.summary}"
                )

    # -----------------------------
    # Detect urgent events
    # -----------------------------

    for m in memories:

        if m.memory_type == "event":

            urgent_events.append(m.summary)

    # -----------------------------
    # Determine focus area
    # -----------------------------

    words = []

    for m in memories:

        tokens = m.summary.lower().split()

        for token in tokens:

            if len(token) > 4:
                words.append(token)

    focus = Counter(words).most_common(1)

    focus_topic = focus[0][0] if focus else None

    return {

        "blocked_tasks": blocked_tasks,
        "urgent_events": urgent_events,
        "decision_dependencies": decision_dependencies,
        "focus_topic": focus_topic

    }