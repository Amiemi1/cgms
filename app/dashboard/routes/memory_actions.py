import asyncio

from fastapi import APIRouter

from app.db.models.memory import Memory
from app.db.session import SessionLocal
from app.services.orchestration.contracts.memory_events import (
    memory_priority_changed_event,
)
from app.services.orchestration.event_bus import DEFAULT_EVENT_BUS


router = APIRouter(prefix="/memory", tags=["Memory Actions"])


def publish_memory_event(event) -> None:
    """
    Publish memory domain events from synchronous route handlers.

    TODO(v1.76):
    Convert memory action routes to async and await DEFAULT_EVENT_BUS.publish()
    directly.
    """

    try:
        asyncio.run(DEFAULT_EVENT_BUS.publish(event))
    except RuntimeError:
        # Compatibility fallback for environments where an event loop
        # may already be running.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(DEFAULT_EVENT_BUS.publish(event))


@router.patch("/{memory_id}/priority")
def update_priority(memory_id: int, priority: int):
    session = SessionLocal()

    try:
        memory = session.get(Memory, memory_id)

        if not memory:
            return {"error": "Memory not found"}

        old_priority = memory.priority
        memory.priority = priority

        session.add(memory)
        session.commit()
        session.refresh(memory)

        event = memory_priority_changed_event(
            memory_id=memory.id,
            source="memory_actions.update_priority",
            old_priority=old_priority,
            new_priority=priority,
        )

        publish_memory_event(event)

        return {
            "message": "Priority updated",
            "memory_id": memory.id,
            "old_priority": old_priority,
            "priority": priority,
            "event_published": True,
            "event_name": event.event_name,
        }

    finally:
        session.close()