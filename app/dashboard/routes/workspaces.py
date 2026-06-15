from fastapi import APIRouter

from app.services.workspace.registry import (

    get_workspaces,

    create_workspace
)

router = APIRouter()


@router.get(
    "/workspaces"
)
def workspaces():

    return get_workspaces()


@router.post(
    "/workspaces"
)
def create(
    payload: dict
):

    workspace_id = payload.get(
        "id"
    )

    return create_workspace(

        workspace_id,

        payload
    )