from sqlmodel import Session

from app.services.detection.orchestrator import detect
from app.db.models.candidate_memory import CandidateMemory
from app.services.workspace.tenant_scope import normalize_workspace_id


def ingest_message(
    session: Session,
    chat_id: int,
    message_id: int,
    text: str,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    # ------------------------------------------------
    # Ignore commands
    # ------------------------------------------------
    if not text or text.startswith("/"):
        return None

    result = detect(text)

    if not result:
        return None

    candidate = CandidateMemory(
        workspace_id=resolved_workspace_id,
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
