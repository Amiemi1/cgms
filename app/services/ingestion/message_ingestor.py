from sqlmodel import Session

from app.services.detection.orchestrator import detect
from app.db.models.candidate_memory import CandidateMemory


def ingest_message(session: Session, chat_id: int, message_id: int, text: str):

    # ------------------------------------------------
    # Ignore commands
    # ------------------------------------------------
    if not text or text.startswith("/"):
        return None

    result = detect(text)

    if not result:
        return None

    candidate = CandidateMemory(
        chat_id=chat_id,
        message_id=message_id,
        summary=result["summary"],
        memory_type=result["type"],
        status="pending"
    )

    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    return candidate