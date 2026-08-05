from sqlmodel import Session

from app.db.session import engine
from app.db.models.memory import Memory
from app.services.memory_intelligence.scoring import (
    calculate_memory_score
)
from app.services.memory_intelligence.score_store import (
    save_score
)
from app.services.workspace.tenant_scope import (
    load_scoped_record,
    normalize_workspace_id,
    TenantScopeError,
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

    workspace_id = event.get(
        "workspace_id"
    )

    try:
        resolved_workspace_id = normalize_workspace_id(
            workspace_id
        )
    except TenantScopeError:
        return {
            "processed": False,
            "reason": "missing_workspace_id",
            "memory_id": memory_id,
        }

    with Session(engine) as session:

        memory = load_scoped_record(
            session,
            Memory,
            memory_id,
            resolved_workspace_id,
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
            score,
            resolved_workspace_id,
        )

        return {
            "processed": True,
            "memory_id": memory_id,
            "score": score
        }
