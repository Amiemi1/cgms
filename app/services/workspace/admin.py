from datetime import datetime

from app.services.workspace.registry import (
    get_workspaces
)


workspace_admin_state = {}


def get_workspace_admin_state():

    workspaces = get_workspaces()

    for workspace_id in workspaces:

        workspace_admin_state.setdefault(
            workspace_id,
            {
                "suspended": False,
                "suspensionReason": None,
                "updatedAt": None
            }
        )

    return workspace_admin_state


def suspend_workspace(
    workspace_id: str,
    reason: str = "manual_admin_action"
):

    get_workspace_admin_state()

    workspace_admin_state[workspace_id] = {
        "suspended": True,
        "suspensionReason": reason,
        "updatedAt": datetime.utcnow().isoformat()
    }

    return workspace_admin_state[workspace_id]


def activate_workspace(
    workspace_id: str
):

    get_workspace_admin_state()

    workspace_admin_state[workspace_id] = {
        "suspended": False,
        "suspensionReason": None,
        "updatedAt": datetime.utcnow().isoformat()
    }

    return workspace_admin_state[workspace_id]