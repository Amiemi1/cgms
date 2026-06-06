from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/recent")
def recent_memories(chat_id: int):

    session = SessionLocal()

    try:

        result = session.execute(text("""
            SELECT id, summary, memory_type
            FROM memory
            WHERE chat_id = :chat_id
            ORDER BY created_at DESC
            LIMIT 20
        """), {"chat_id": chat_id})

        rows = result.fetchall()

        return [
            {
                "id": r.id,
                "summary": r.summary,
                "type": r.memory_type
            }
            for r in rows
        ]

    finally:
        session.close()