from fastapi import APIRouter
from datetime import datetime


router = APIRouter()


quarantine_state = {
    "active": False,
    "subsystems": [],
    "reason": None,
    "updatedAt": None
}


@router.get("/runtime/quarantine")
def get_quarantine():

    return quarantine_state


@router.post("/runtime/quarantine")
def update_quarantine(
    payload: dict
):

    subsystem = payload.get(
        "subsystem",
        "unknown"
    )

    action = payload.get(
        "action",
        "quarantine"
    )

    reason = payload.get(
        "reason",
        "manual_governance_action"
    )

    if action == "quarantine":

        if subsystem not in quarantine_state["subsystems"]:

            quarantine_state["subsystems"].append(
                subsystem
            )

    elif action == "release":

        quarantine_state["subsystems"] = [
            s for s in quarantine_state["subsystems"]
            if s != subsystem
        ]

    quarantine_state["active"] = (
        len(quarantine_state["subsystems"]) > 0
    )

    quarantine_state["reason"] = reason

    quarantine_state["updatedAt"] = (
        datetime.utcnow()
        .isoformat()
    )

    return {
        "ok": True,
        "quarantine": quarantine_state
    }