from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app.db.session import engine
from app.db.models.memory import Memory

from app.services.memory_intelligence.scoring import calculate_memory_score
from app.services.memory_intelligence.events import process_memory_event
from app.services.memory_intelligence.score_store import (
    get_score,
    get_all_scores,
)

from app.services.memory_intelligence.hooks import (
    handle_memory_intelligence_hook
)

from app.services.memory_intelligence.score_store import (
    get_score,
    get_all_scores,
    get_memory_intelligence_dashboard,
)

router = APIRouter(
    prefix="/memory",
    tags=["Memory Intelligence"]
)


@router.get("/intelligence/{memory_id}")
def get_memory_intelligence(memory_id: int):

    with Session(engine) as session:

        memory = session.get(Memory, memory_id)

        if memory is None:
            raise HTTPException(
                status_code=404,
                detail="Memory not found"
            )

        return calculate_memory_score(memory)


@router.get("/explain/{memory_id}")
def explain_memory(memory_id: int):

    with Session(engine) as session:

        memory = session.get(Memory, memory_id)

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
def memory_event(payload: dict):

    return process_memory_event(payload)


@router.get("/score-cache/{memory_id}")
def score_cache(memory_id: int):

    score = get_score(memory_id)

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
def all_score_cache():

    return get_all_scores()

@router.get("/dashboard")
def memory_dashboard():

    return get_memory_intelligence_dashboard()

@router.post("/hook")
def memory_intelligence_hook(payload: dict):

    return handle_memory_intelligence_hook(
        payload.get("event"),
        payload.get("memory_id")
    )