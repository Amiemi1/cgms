from fastapi import APIRouter

from app.services.connectors.registry import (
    get_connectors,
    update_connector
)

router = APIRouter()


@router.get(
    "/connectors"
)
def connectors():

    return get_connectors()


@router.post(
    "/connectors/{name}"
)
def update(
    name: str,
    payload: dict
):

    return update_connector(
        name,
        payload
    )