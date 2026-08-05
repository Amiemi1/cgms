from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.goal import Goal
from app.services.intelligence.prioritization_service import (
    get_prioritized_tasks,
    get_next_action,
)
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import get_current_workspace_id


router = APIRouter(prefix="/dashboard", tags=["Intelligence"])


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



@router.get("/next-action/{chat_id}")
def next_action(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        tasks = get_prioritized_tasks(
            session,
            chat_id,
            workspace_id,
            limit=50,
        )
        print("API TASKS:", tasks)

        result = get_next_action(
            session,
            chat_id,
            workspace_id,
        )
        print("API NEXT ACTION:", result)

        # 🔥 FORCE JSON RESPONSE
        return JSONResponse(content=result or {})

    finally:
        session.close()


@router.get("/next-action/{chat_id}")
def next_action(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):
    ...


# 🔥 NEW ENDPOINT
@router.get("/intelligence/goals/{chat_id}")
def get_intelligence_goals(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        goals = session.exec(
            select(Goal).where(
                Goal.workspace_id == workspace_id,
                Goal.chat_id == chat_id,
            )
        ).all()

        return goals

    finally:
        session.close()


@router.get("/priorities/{chat_id}")
def priorities(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:
        result = get_prioritized_tasks(
            session,
            chat_id,
            workspace_id,
        )
        print("API PRIORITIES:", result)
        return result or []
    finally:
        session.close()
