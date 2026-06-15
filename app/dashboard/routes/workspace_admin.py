from fastapi import APIRouter

from app.services.workspace.admin import (
    get_workspace_admin_state,
    suspend_workspace,
    activate_workspace
)


router = APIRouter()


@router.get("/workspace/admin")
def admin_state():

    return get_workspace_admin_state()


@router.post("/workspace/admin/{workspace_id}/suspend")
def suspend(
    workspace_id: str,
    payload: dict
):

    return suspend_workspace(
        workspace_id,
        payload.get(
            "reason",
            "manual_admin_action"
        )
    )


@router.post("/workspace/admin/{workspace_id}/activate")
def activate(
    workspace_id: str
):

    return activate_workspace(
        workspace_id
    )