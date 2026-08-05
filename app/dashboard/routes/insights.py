from fastapi import APIRouter, Depends

from app.services.insights.insight_engine import generate_insights
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import get_current_workspace_id

router = APIRouter()


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



@router.get("/insights/{chat_id}")
def get_insights(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    try:

        insights = generate_insights(
            chat_id,
            workspace_id,
        )

        return {
            "chat_id": chat_id,
            "insights": insights
        }

    except Exception as e:

        print("INSIGHTS ERROR:", e)

        return {
            "error": str(e)
        }
