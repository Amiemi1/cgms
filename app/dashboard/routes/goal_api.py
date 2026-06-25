from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal
from app.db.models.goal import Goal


router = APIRouter()


@router.get("/dashboard/goals/{chat_id}")
def get_goals(
    chat_id: int,
    limit: int = 20
):

    db = SessionLocal()

    try:

        goals = (
            db.query(Goal)
            .filter(
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