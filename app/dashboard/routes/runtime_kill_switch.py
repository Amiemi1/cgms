from fastapi import APIRouter
from datetime import datetime


router = APIRouter()

kill_switch = {
    "enabled": False,
    "reason": None,
    "updatedAt": None
}


@router.get("/runtime/kill-switch")
def get_kill_switch():

    return kill_switch


@router.post("/runtime/kill-switch")
def update_kill_switch(
    payload: dict
):

    kill_switch["enabled"] = bool(
        payload.get("enabled", False)
    )

    kill_switch["reason"] = payload.get(
        "reason",
        "manual_update"
    )

    kill_switch["updatedAt"] = (
        datetime.utcnow()
        .isoformat()
    )

    return {
        "ok": True,
        "killSwitch": kill_switch
    }