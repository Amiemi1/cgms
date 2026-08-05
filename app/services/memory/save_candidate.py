from app.db.session import SessionLocal
from app.db.models.candidate_memory import CandidateMemory
from app.services.workspace.tenant_scope import normalize_workspace_id


def save_candidate(
    chat_id: int,
    message_id: int,
    memory_type: str,
    summary: str,
    original_text: str,
    *,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    session = SessionLocal()

    try:
        candidate = CandidateMemory(
            workspace_id=resolved_workspace_id,
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
