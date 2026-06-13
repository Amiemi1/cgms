from fastapi import APIRouter

from app.services.connectors.health import (
    connector_health
)

router = APIRouter()


@router.get(
    "/connectors/health"
)
def health():

    return connector_health()