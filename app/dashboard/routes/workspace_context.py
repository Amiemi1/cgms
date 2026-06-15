from fastapi import APIRouter

from app.services.workspace.context import (

    get_workspace,

    set_workspace
)

router = APIRouter()


@router.get(
    "/workspace/context"
)
def context():

    return get_workspace()


@router.post(
    "/workspace/context"
)
def switch(
    payload: dict
):

    return set_workspace(

        payload.get(
            "workspace"
        )
    )