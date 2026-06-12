from fastapi import APIRouter
from datetime import datetime


router = APIRouter()

runtime_state = {
    "mode": "healthy"
}


@router.post("/runtime/command")
def runtime_command(
    payload: dict
):

    command = payload.get(
        "command",
        "noop"
    )

    if command == "pause":

        runtime_state["mode"] = "paused"

    elif command == "resume":

        runtime_state["mode"] = "healthy"

    elif command == "maintenance":

        runtime_state["mode"] = "maintenance"

    return {
        "ok": True,
        "command": command,
        "mode": runtime_state["mode"],
        "timestamp":
            datetime.utcnow()
            .isoformat()
    }


@router.get("/runtime/command")
def runtime_status():

    return runtime_state