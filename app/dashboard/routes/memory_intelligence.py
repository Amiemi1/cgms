from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import engine
from app.db.models.memory import Memory

from app.services.memory_intelligence.scoring import calculate_memory_score
from app.services.memory_intelligence.events import process_memory_event
from app.services.memory_intelligence.hooks import (
    handle_memory_intelligence_hook
)
from app.services.memory_intelligence.score_store import (
    get_score,
    get_all_scores,
    get_memory_intelligence_dashboard,
)
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import (
    get_current_workspace_id,
    load_scoped_record,
)


router = APIRouter(
    prefix="/memory",
    tags=["Memory Intelligence"]
)


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



@router.get("/intelligence/{memory_id}")
def get_memory_intelligence(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    with Session(engine) as session:

        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if memory is None:
            raise HTTPException(
                status_code=404,
                detail="Memory not found"
            )

        return calculate_memory_score(memory)


@router.get("/explain/{memory_id}")
def explain_memory(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    with Session(engine) as session:

        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            workspace_id,
        )

        if memory is None:
            raise HTTPException(
                status_code=404,
                detail="Memory not found"
            )

        score = calculate_memory_score(memory)

        return {
            "memory_id": memory_id,
            "score": score,
            "explainability": score.factors,
        }


@router.post("/event")
def memory_event(
    payload: dict,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):
    scoped_payload = dict(payload)
    scoped_payload["workspace_id"] = workspace_id
    return process_memory_event(scoped_payload)


@router.get("/score-cache/{memory_id}")
def score_cache(
    memory_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    score = get_score(
        memory_id,
        workspace_id,
    )

    if score is None:
        return {
            "cached": False,
            "memory_id": memory_id,
        }

    return {
        "cached": True,
        "memory_id": memory_id,
        "score": score,
    }


@router.get("/score-cache")
def all_score_cache(
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    return get_all_scores(workspace_id)


@router.get("/dashboard")
def memory_dashboard(
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    return get_memory_intelligence_dashboard(
        workspace_id
    )


@router.post("/hook")
def memory_intelligence_hook(
    payload: dict,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    return handle_memory_intelligence_hook(
        payload.get("event"),
        payload.get("memory_id"),
        workspace_id,
    )
