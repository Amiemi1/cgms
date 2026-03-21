from app.db.session import SessionLocal
from app.db.models.message import Message


def save_message(
    telegram_message_id: int,
    chat_id: int,
    user_id: int,
    chat_type: str,
    text: str,
):
    session = SessionLocal()

    try:
        message = Message(
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