from fastapi import APIRouter
from sqlmodel import select
from app.db.session import SessionLocal
from app.db.models.goal import Goal
from app.services.intelligence.prioritization_service import (
    get_prioritized_tasks,
    get_next_action
)

router = APIRouter(prefix="/dashboard", tags=["Intelligence"])


from fastapi.responses import JSONResponse

@router.get("/next-action/{chat_id}")
def next_action(chat_id: int):

    session = SessionLocal()

    try:
        tasks = get_prioritized_tasks(session, chat_id, limit=50)
        print("API TASKS:", tasks)

        result = get_next_action(session, chat_id)
        print("API NEXT ACTION:", result)

        # 🔥 FORCE JSON RESPONSE
        return JSONResponse(content=result or {})

    finally:
        session.close()
    ...


@router.get("/next-action/{chat_id}")
def next_action(chat_id: int):
    ...


# 🔥 NEW ENDPOINT
@router.get("/intelligence/goals/{chat_id}")
def get_intelligence_goals(chat_id: int):

    session = SessionLocal()

    try:
        goals = session.exec(
            select(Goal).where(Goal.chat_id == chat_id)
        ).all()

        return goals

    finally:
        session.close()

@router.get("/priorities/{chat_id}")
def priorities(chat_id: int):

    session = SessionLocal()

    try:
        result = get_prioritized_tasks(session, chat_id)
        print("API PRIORITIES:", result)
        return result or []
    finally:
        session.close()