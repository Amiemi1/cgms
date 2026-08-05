import asyncio

from fastapi import APIRouter, Depends

from app.db.models.memory import Memory
from app.db.session import SessionLocal
from app.services.orchestration.contracts.memory_events import (
    memory_priority_changed_event,
)
from app.services.orchestration.event_bus import DEFAULT_EVENT_BUS
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import (
    get_current_workspace_id,
    load_scoped_record,
)


router = APIRouter(
    prefix="/memory",
    tags=["Memory Actions"],
)


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



def publish_memory_event(event):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(
            DEFAULT_EVENT_BUS.publish(event)
        )
        return

    loop.create_task(
        DEFAULT_EVENT_BUS.publish(event)
    )


@router.patch("/{memory_id}/priority")
def update_priority(
    memory_id: int,
    priority: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):
    session = SessionLocal()

    try:
        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if not memory:
            return {"error": "Memory not found"}

        old_priority = memory.priority
        memory.priority = priority

        session.add(memory)
        session.commit()
        session.refresh(memory)

        event = memory_priority_changed_event(
            memory_id=memory.id,
            workspace_id=workspace_id,
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
