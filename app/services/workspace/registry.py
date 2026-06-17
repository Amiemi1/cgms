from app.services.persistence.workspace_store import (
    load_workspaces,
    save_workspaces
)


WORKSPACES = load_workspaces() or {
    "default": {
        "name": "Default Workspace",
        "status": "active",
        "createdBy": "system"
    }
}


def get_workspaces():

    return WORKSPACES


def create_workspace(
    workspace_id,
    payload
):

    WORKSPACES[
        workspace_id
    ] = {

        "name":
            payload.get(
                "name"
            ),

        "status":
            "active",

        "createdBy":
            payload.get(
                "createdBy",
                "unknown"
            )
    }

    save_workspaces(
        WORKSPACES
    )

    return WORKSPACES[
        workspace_id
    ]