WORKSPACES = {
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

    return WORKSPACES[
        workspace_id
    ]