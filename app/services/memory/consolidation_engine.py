from sqlmodel import select

from app.db.models.memory import Memory
from app.services.memory.scope import (
    identity_scope_from_record,
    orm_identity_predicate,
)


def consolidate_memory(session, new_memory):

    """
    Consolidate duplicate memories by increasing cluster_count
    instead of deleting records during flush cycle.
    """

    scope = identity_scope_from_record(
        new_memory
    )

    existing = session.exec(
        select(Memory).where(
            Memory.workspace_id
            == scope.workspace_id,
            orm_identity_predicate(
                Memory,
                scope,
            ),
            Memory.summary
            == new_memory.summary,
            Memory.id
            != new_memory.id,
        )
    ).first()

    if existing:

        # Increase cluster count
        existing.cluster_count += 1

        session.add(existing)
        session.commit()

        print("MEMORY MERGED:", existing.summary)

        return existing

    return new_memory
