from fastapi import APIRouter, Depends, HTTPException

from app.db.models.goal import Goal
from app.db.session import SessionLocal
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



@router.get("/dashboard/goals/{chat_id}")
def get_goals(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
    limit: int = 20,
):

    db = SessionLocal()

    try:

        goals = (
            db.query(Goal)
            .filter(
                Goal.workspace_id == workspace_id,
                Goal.chat_id == chat_id,
                Goal.status != "deleted"
            )
            .order_by(
                Goal.created_at.desc()
            )
            .limit(
                limit
            )
            .all()
        )

        clean_goals = []

        seen = set()

        for goal in goals:

            name = str(
                getattr(
                    goal,
                    "name",
                    ""
                )
            ).strip()

            if not name:
                continue

            if name.isdigit():
                continue

            normalized = name.lower()

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            clean_goals.append(
                {
                    "id":
                        goal.id,

                    "name":
                        name,

                    "description":
                        getattr(
                            goal,
                            "description",
                            None
                        ),

                    "status":
                        getattr(
                            goal,
                            "status",
                            "active"
                        ),

                    "chat_id":
                        goal.chat_id,

                    "created_at":
                        str(
                            goal.created_at
                        )
                }
            )

        return clean_goals

    except Exception as e:

        print(
            "GOALS API ERROR:",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load goals"
        )

    finally:

        db.close()
