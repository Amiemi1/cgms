from sqlmodel import Session

from app.db.models.learning import Learning
from app.db.models.memory import Memory
from app.services.workspace.tenant_scope import (
    load_scoped_record,
    normalize_workspace_id,
)


def record_action(
    session: Session,
    chat_id: int,
    memory_id: int,
    action: str,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    memory = load_scoped_record(
        session,
        Memory,
        memory_id,
        resolved_workspace_id,
    )

    if memory is None:
        return None

    entry = Learning(
        workspace_id=resolved_workspace_id,
        chat_id=chat_id,
        memory_id=memory_id,
        action=action
    )

    session.add(entry)
    session.commit()

    return entry


def adjust_priority(memory: Memory, learning_data: list):
    """
    Adjust priority based on user behavior.
    """

    score = memory.priority

    for entry in learning_data:
        if (
            entry.workspace_id == memory.workspace_id
            and entry.memory_id == memory.id
        ):

            if entry.action == "completed":
                score += 10

            elif entry.action == "ignored":
                score -= 10

            elif entry.action == "delayed":
                score += 5

    return max(0, min(score, 100))
