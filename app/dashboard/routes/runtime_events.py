from fastapi import APIRouter
from app.services.orchestration.event_router import (
    route_memory_update,
    route_runtime_state_change,
    route_incident
)

router = APIRouter()


@router.post("/runtime/event")
async def runtime_event(
    payload: dict
):

    event = payload.get(
        "event"
    )

    data = payload.get(
        "payload",
        {}
    )

    if event == "memory_changed":

        await route_memory_update(
            data
        )

    elif event == "runtime_state_changed":

        await route_runtime_state_change(
            data
        )

    elif event == "incident":

        await route_incident(
            data
        )

    return {
        "ok": True
    }