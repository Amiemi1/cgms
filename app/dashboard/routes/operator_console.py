from fastapi import APIRouter

from app.services.workspace.registry import get_workspaces
from app.services.connectors.registry import get_connectors
from app.services.connectors.event_ingestion import INGESTED_EVENTS
from app.dashboard.routes.ops import OPS_ERRORS


router = APIRouter()


# ====================================================
# OPERATOR CONSOLE
# ====================================================

@router.get("/operator/console")
def operator_console():

    workspaces = get_workspaces()

    connectors = get_connectors()

    connected = [
        c
        for c in connectors.values()
        if c.get("enabled")
    ]

    return {

        "system": "CGMS",

        "version": "v1.71",

        "status": "operational",

        "summary": {

            "workspaces":
                len(workspaces),

            "connectors":
                len(connectors),

            "connectedConnectors":
                len(connected),

            "events":
                len(
                    INGESTED_EVENTS
                ),

            "errors":
                len(
                    OPS_ERRORS
                )
        },

        "sections": [

            "health",

            "events",

            "latency",

            "errors",

            "runtimeTimeline",

            "actions"
        ]
    }


# ====================================================
# OPERATOR ACTIONS
# ====================================================

@router.post("/operator/action")
def operator_action(payload: dict):

    action = payload.get(
        "action",
        ""
    ).lower()

    if action == "refresh":

        return {

            "ok": True,

            "action":
                action,

            "message":
                "Runtime refresh requested"
        }

    elif action == "pause":

        return {

            "ok": True,

            "action":
                action,

            "message":
                "Runtime pause requested"
        }

    elif action == "resume":

        return {

            "ok": True,

            "action":
                action,

            "message":
                "Runtime resume requested"
        }

    return {

        "ok": False,

        "action":
            action,

        "message":
            "Unknown operator action"
    }