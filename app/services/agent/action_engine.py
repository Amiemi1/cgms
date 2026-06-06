# =====================================================
# ACTION ENGINE
# Executes a plan by creating task memories
# =====================================================

from sqlmodel import select

from app.db.models.memory import Memory


def execute_plan(session, chat_id: int, plan):

    created = []

    for step in plan:

        existing = session.exec(
            select(Memory).where(
                Memory.chat_id == chat_id,
                Memory.summary == step,
                Memory.memory_type == "task"
            )
        ).first()

        if existing:
            continue

        memory = Memory(
            chat_id=chat_id,
            summary=step,
            memory_type="task",
            status="active",
            priority=50
        )

        session.add(memory)
        created.append(step)

    session.commit()

    return created