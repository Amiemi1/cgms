from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def analyze_plan_risk(session, chat_id: int, plan):

    print("RISK ENGINE RUNNING")

    warnings = []

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    print("TOTAL MEMORIES:", len(memories))

    tasks = [m for m in memories if m.memory_type == "task"]
    decisions = [m for m in memories if m.memory_type == "decision"]
    events = [m for m in memories if m.memory_type == "event"]

    print("TASKS:", len(tasks))
    print("DECISIONS:", len(decisions))
    print("EVENTS:", len(events))

    # --------------------------------
    # Risk 1: Tasks but no decisions
    # --------------------------------

    if tasks and not decisions:

        warnings.append(
            "⚠️ Tasks exist but no decisions recorded. Some work may require approvals."
        )

    # --------------------------------
    # Risk 2: Events but no tasks
    # --------------------------------

    if events and not tasks:

        warnings.append(
            "⚠️ Upcoming events exist but no preparation tasks were found."
        )

    # --------------------------------
    # Risk 3: Decision dependencies
    # --------------------------------

    relationships = session.exec(
        select(MemoryRelationship)
    ).all()

    for r in relationships:

        if r.relationship_type == "resolves":

            decision = next((m for m in decisions if m.id == r.source_memory_id), None)
            task = next((m for m in tasks if m.id == r.target_memory_id), None)

            if decision and task:

                warnings.append(
                    f"⚠️ Task '{task.summary}' depends on decision '{decision.summary}'."
                )

    print("WARNINGS:", warnings)

    return warnings