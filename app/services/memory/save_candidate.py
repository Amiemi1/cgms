from app.db.session import SessionLocal
from app.db.models.candidate_memory import CandidateMemory


def save_candidate(
    chat_id: int,
    message_id: int,
    memory_type: str,
    summary: str,
    original_text: str,
):
    session = SessionLocal()

    try:
        candidate = CandidateMemory(
            chat_id=chat_id,
            message_id=message_id,
            memory_type=memory_type,
            summary=summary,
            original_text=original_text,
            status="pending",
        )

        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        return candidate

    finally:
        session.close()