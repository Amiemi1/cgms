from fastapi import APIRouter
from app.services.orchestration.event_router import (
    route_memory_update,
    route_runtime_state_change,
    route_incident
)

from app.dashboard.runtime.incident_assessor import (
    assess_runtime_impact
)

router = APIRouter()


@router.post("/runtime/event")
async def runtime_event(
    payload: dict
):

    event = payload.get("event")
    data = payload.get("payload", {})

    impact = assess_runtime_impact({
        "eventName": event,
        "payload": data
    })

    data = {
        **data,
        "impact": impact
    }

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