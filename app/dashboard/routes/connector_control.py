from fastapi import APIRouter

from app.services.connectors.activation import (

    activate_connector,

    deactivate_connector
)

router = APIRouter()


@router.post(
    "/connectors/{name}/activate"
)
def activate(
    name: str
):

    return activate_connector(
        name
    )


@router.post(
    "/connectors/{name}/deactivate"
)
def deactivate(
    name: str
):

    return deactivate_connector(
        name
    )