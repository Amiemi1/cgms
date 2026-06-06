from fastapi import APIRouter

from app.db.session import SessionLocal
from app.services.intelligence.intelligence_engine import generate_intelligence_report

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"]
)


@router.get("/")
def intelligence(chat_id: int):

    session = SessionLocal()

    try:

        report = generate_intelligence_report(session, chat_id)

        return {"report": report}

    finally:
        session.close()