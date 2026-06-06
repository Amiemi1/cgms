
from sqlmodel import select
from collections import Counter
from datetime import datetime, timedelta

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def determine_next_action(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    memory_map = {m.id: m for m in memories}

    blocked_tasks = []
    urgent_tasks = []

    now = datetime.utcnow()

    # ------------------------------------------------
    # Detect tasks blocked by decisions
    # ------------------------------------------------

    for rel in relationships:

        if rel.relationship_type == "resolves":

            decision = memory_map.get(rel.source_memory_id)
            task = memory_map.get(rel.target_memory_id)

            if decision and task:

                blocked_tasks.append({
                    "task": task.summary,
                    "decision": decision.summary
                })

    # ------------------------------------------------
    # Detect urgent tasks (linked to upcoming events)
    # ------------------------------------------------

    upcoming_events = [
        m for m in memories
        if m.memory_type == "event"
        and m.reminder_time
        and m.reminder_time < now + timedelta(hours=24)
    ]

    event_ids = [e.id for e in upcoming_events]

    for rel in relationships:

        if rel.relationship_type == "triggered_by":

            task = memory_map.get(rel.source_memory_id)
            event = memory_map.get(rel.target_memory_id)

            if task and event and event.id in event_ids:

                urgent_tasks.append(task.summary)

    # ------------------------------------------------
    # Determine next action
    # ------------------------------------------------

    if urgent_tasks:

        task = urgent_tasks[0]

        return {
            "action": task,
            "reason": "Task required for an upcoming event."
        }

    if blocked_tasks:

        item = blocked_tasks[0]

        return {
            "action": f"Resolve decision: {item['decision']}",
            "reason": f"Task blocked: {item['task']}"
        }

    # ------------------------------------------------
    # Fallback: most frequent topic
    # ------------------------------------------------

    words = []

    for m in memories:

        tokens = m.summary.lower().split()

        for token in tokens:

            if len(token) > 4:
                words.append(token)

    focus = Counter(words).most_common(1)

    if focus:

        return {
            "action": f"Continue work related to '{focus[0][0]}'",
            "reason": "Current dominant focus area."
        }

    return None