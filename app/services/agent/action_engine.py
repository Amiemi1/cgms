# =====================================================
# ACTION ENGINE
# Executes a plan by creating task memories
# =====================================================

from sqlmodel import select

from app.db.models.memory import Memory
from app.services.workspace.tenant_scope import normalize_workspace_id


def execute_plan(
    session,
    chat_id: int,
    plan,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    created = []

    for step in plan:

        existing = session.exec(
            select(Memory).where(
                Memory.workspace_id == resolved_workspace_id,
                Memory.chat_id == chat_id,
                Memory.summary == step,
                Memory.memory_type == "task"
            )
        ).first()

        if existing:
            continue

        memory = Memory(
            workspace_id=resolved_workspace_id,
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
