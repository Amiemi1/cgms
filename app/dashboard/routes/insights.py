from fastapi import APIRouter

from app.services.insights.insight_engine import generate_insights

router = APIRouter()


@router.get("/insights/{chat_id}")
def get_insights(chat_id: int):

    try:

        insights = generate_insights(chat_id)

        return {
            "chat_id": chat_id,
            "insights": insights
        }

    except Exception as e:

        print("INSIGHTS ERROR:", e)

        return {
            "error": str(e)
        }