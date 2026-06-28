from fastapi import APIRouter

from app.db.session import SessionLocal
from app.db.models.memory import Memory

from app.services.memory_intelligence.hooks import (
    handle_memory_intelligence_hook
)


router = APIRouter(prefix="/memory", tags=["Memory Actions"])


def recalculate_memory_intelligence(event_name: str, memory_id: int):
    try:
        handle_memory_intelligence_hook(event_name, memory_id)
    except Exception as e:
        print("MEMORY INTELLIGENCE HOOK ERROR:", e)


@router.patch("/{memory_id}/priority")
def update_priority(memory_id: int, priority: int):

    session = SessionLocal()

    try:
        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        memory.priority = priority

        session.add(memory)
        session.commit()

        recalculate_memory_intelligence(
            "MemoryUpdated",
            memory.id
        )

        return {
            "message": "Priority updated",
            "memory_id": memory.id,
            "priority": priority,
        }

    finally:
        session.close()