from fastapi import APIRouter
from app.services.orchestration.event_router import (
    route_memory_update,
    route_runtime_state_change,
    route_incident
)

from app.dashboard.runtime.incident_assessor import (
    assess_runtime_impact
)

from app.services.explainability.explainability_engine import (
    explain_runtime_decision
)

from app.services.orchestration.session_store import (
    store_session_event
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

    explanation = explain_runtime_decision(
    event,
    data
)

    data = {
        **data,
        "explanation": explanation
    }

    store_session_event(
        event,
        data
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