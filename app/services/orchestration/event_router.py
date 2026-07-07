from app.services.orchestration.event_registry import (
    event_registry
)


# ======================================
# MEMORY EVENTS
# ======================================

async def route_memory_update(
    payload
):

    await event_registry.publish(
        "memory.changed",
        payload
    )


# ======================================
# RUNTIME EVENTS
# ======================================

async def route_runtime_state_change(
    payload
):

    state = payload.get(
        "state"
    )

    if state == "degraded":

        await event_registry.publish(
            "runtime_degraded",
            payload
        )

    elif state == "healthy":

        await event_registry.publish(
            "runtime_restored",
            payload
        )


# ======================================
# INCIDENT EVENTS
# (foundation for Incident Impact Assessment)
# ======================================

async def route_incident(
    payload
):

    severity = payload.get(
        "severity",
        "low"
    )

    await event_registry.publish(
        f"incident_{severity}",
        payload
    )