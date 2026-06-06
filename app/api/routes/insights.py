from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.insight import Insight

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/{chat_id}")
def get_insights(chat_id: int):

    session = SessionLocal()

    try:

        insights = session.exec(
            select(Insight)
            .where(Insight.chat_id == chat_id)
            .order_by(Insight.created_at.desc())
        ).all()

        return insights

    finally:
        session.close()