from app.db.session import SessionLocal
from app.db.models.message import Message
from app.services.workspace.tenant_scope import normalize_workspace_id


def save_message(
    telegram_message_id: int,
    chat_id: int,
    user_id: int,
    chat_type: str,
    text: str,
    *,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    session = SessionLocal()

    try:
        message = Message(
            workspace_id=resolved_workspace_id,
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
            user_id=user_id,
            chat_type=chat_type,
            text=text,
        )

        session.add(message)
        session.commit()

    finally:
        session.close()
