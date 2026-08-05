from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship
from app.services.retrieval.vector_search import vector_search
from app.services.workspace.tenant_scope import inherit_workspace_id


def link_memories(session, new_memory):

    workspace_id = inherit_workspace_id(new_memory)

    # ------------------------------------------------
    # RULE RELATIONSHIPS
    # ------------------------------------------------

    recent_memories = session.exec(
        select(Memory)
        .where(
            Memory.workspace_id == workspace_id,
            Memory.chat_id == new_memory.chat_id,
        )
        .order_by(Memory.created_at.desc())
        .limit(10)
    ).all()

    for memory in recent_memories:

        if memory.id == new_memory.id:
            continue

        relationship_type = None

        if new_memory.memory_type == "task" and memory.memory_type == "event":
            relationship_type = "triggered_by"

        elif new_memory.memory_type == "decision" and memory.memory_type == "task":
            relationship_type = "resolves"

        if not relationship_type:
            continue

        existing = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.workspace_id == workspace_id,
                MemoryRelationship.source_memory_id == new_memory.id,
                MemoryRelationship.target_memory_id == memory.id,
                MemoryRelationship.relationship_type == relationship_type
            )
        ).first()

        if existing:
            continue

        relationship = MemoryRelationship(
            workspace_id=workspace_id,
            source_memory_id=new_memory.id,
            target_memory_id=memory.id,
            relationship_type=relationship_type
        )

        session.add(relationship)

    session.commit()

    # ------------------------------------------------
    # SEMANTIC RELATIONSHIPS
    # ------------------------------------------------

    if new_memory.embedding is None:
        return

    results = vector_search(
        session=session,
        embedding=new_memory.embedding,
        chat_id=new_memory.chat_id,
        workspace_id=workspace_id,
        limit=5
    )

    for row in results:

        memory_id = row[0]
        score = row[3]

        if memory_id == new_memory.id:
            continue

        if score < 0.80:
            continue

        existing = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.workspace_id == workspace_id,
                MemoryRelationship.source_memory_id == new_memory.id,
                MemoryRelationship.target_memory_id == memory_id,
                MemoryRelationship.relationship_type == "semantic_related"
            )
        ).first()

        if existing:
            continue

        relationship = MemoryRelationship(
            workspace_id=workspace_id,
            source_memory_id=new_memory.id,
            target_memory_id=memory_id,
            relationship_type="semantic_related"
        )

        session.add(relationship)

    session.commit()
