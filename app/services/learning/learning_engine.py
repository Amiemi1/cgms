from sqlmodel import Session

from app.db.models.learning import Learning
from app.db.models.memory import Memory


def record_action(session: Session, chat_id: int, memory_id: int, action: str):
    entry = Learning(
        chat_id=chat_id,
        memory_id=memory_id,
        action=action
    )

    session.add(entry)
    session.commit()


def adjust_priority(memory: Memory, learning_data: list):
    """
    Adjust priority based on user behavior.
    """

    score = memory.priority

    for entry in learning_data:
        if entry.memory_id == memory.id:

            if entry.action == "completed":
                score += 10

            elif entry.action == "ignored":
                score -= 10

            elif entry.action == "delayed":
                score += 5

    return max(0, min(score, 100))