from fastapi import APIRouter

from app.services.workspace.metrics import (
    workspace_metrics
)

router = APIRouter()


@router.get(
    "/workspace/metrics"
)
def metrics():

    return workspace_metrics()