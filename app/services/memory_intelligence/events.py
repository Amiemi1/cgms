from sqlmodel import Session

from app.db.session import engine
from app.db.models.memory import Memory
from app.services.memory_intelligence.scoring import (
    calculate_memory_score
)
from app.services.memory_intelligence.score_store import (
    save_score
)


def process_memory_event(
    event: dict
):

    memory_id = event.get(
        "memory_id"
    )

    if memory_id is None:

        return {
            "processed": False,
            "reason": "missing_memory_id"
        }

    with Session(engine) as session:

        memory = session.get(
            Memory,
            memory_id
        )

        if memory is None:

            return {
                "processed": False,
                "reason": "memory_not_found",
                "memory_id": memory_id
            }

        score = calculate_memory_score(
            memory
        ).model_dump()

        save_score(
            memory_id,
            score
        )

        return {
            "processed": True,
            "memory_id": memory_id,
            "score": score
        }