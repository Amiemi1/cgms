from fastapi import APIRouter
from app.db.session import SessionLocal
from app.db.models.goal import Goal

router = APIRouter(prefix="/dashboard", tags=["Goal"])


@router.post("/goal/{chat_id}")
def create_goal(chat_id: int, name: str):

    session = SessionLocal()

    try:
        g = Goal(name=name, chat_id=chat_id)
        session.add(g)
        session.commit()
        session.refresh(g)

        return g

    finally:
        session.close()