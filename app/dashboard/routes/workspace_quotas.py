from fastapi import APIRouter

from app.services.workspace.quotas import (
    get_workspace_quotas,
    get_workspace_quota,
    set_workspace_quota
)


router = APIRouter()


@router.get("/workspace/quotas")
def all_quotas():

    return get_workspace_quotas()


@router.get("/workspace/quotas/{workspace_id}")
def quota(
    workspace_id: str
):

    return get_workspace_quota(
        workspace_id
    )


@router.post("/workspace/quotas/{workspace_id}")
def update_quota(
    workspace_id: str,
    payload: dict
):

    return set_workspace_quota(
        workspace_id,
        payload
    )