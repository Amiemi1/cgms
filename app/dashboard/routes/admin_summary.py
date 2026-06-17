from fastapi import APIRouter

from app.services.workspace.registry import (
    get_workspaces
)

from app.services.connectors.registry import (
    get_connectors
)

from app.services.workspace.metrics import (
    workspace_metrics
)


router = APIRouter()


@router.get(
    "/admin/summary"
)
def admin_summary():

    workspaces = get_workspaces()

    connectors = get_connectors()

    metrics = workspace_metrics()

    connected = len([

        c

        for c

        in connectors.values()

        if c.get(
            "enabled"
        )

    ])

    return {

        "platform":

            "CGMS",

        "workspaces":

            len(
                workspaces
            ),

        "connectors":

            len(
                connectors
            ),

        "connected":

            connected,

        "workspaceMetrics":

            metrics,

        "ready":

            True
    }