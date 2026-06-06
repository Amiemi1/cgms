# ==============================================================
# MEMORY RETRIEVAL SERVICE
# ==============================================================

from sqlmodel import select
from app.db.models.memory import Memory
from app.services.intelligence.memory_intelligence_service import score_memory


def search_memory(session, chat_id, query):

    q = query.lower()

    memories = session.exec(
        select(Memory)
        .where(Memory.chat_id == chat_id)
        .order_by(Memory.created_at.desc())
        .limit(50)
    ).all()

    results = []

    for memory in memories:

        if q in memory.summary.lower():
            results.append(memory)

    return results