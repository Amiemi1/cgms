from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship

from app.services.detection.orchestrator import detect
from app.services.retrieval.embedding_service import generate_embedding

from app.services.graph.vector_graph import create_vector_relationships
from app.services.insights.insight_engine import generate_insights
from app.services.workspace.tenant_scope import normalize_workspace_id


def process_message(
    chat_id: int,
    text: str,
    workspace_id: str,
):

    session = SessionLocal()
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    try:

        # -----------------------------
        # Detect memory type
        # -----------------------------

        detection = detect(text)

        if not detection:
            return None

        memory_type = detection["type"]
        summary = detection["summary"]

        # -----------------------------
        # Generate embedding
        # -----------------------------

        embedding = generate_embedding(summary)

        # -----------------------------
        # Save memory
        # -----------------------------

        embedding = generate_embedding(summary)

        memory = Memory(
            workspace_id=resolved_workspace_id,
            chat_id=chat_id,
            summary=summary,
            memory_type=memory_type,
            embedding=embedding
        )

        session.add(memory)
        session.commit()
        session.refresh(memory)

        # -----------------------------
        # Rule-based relationships
        # -----------------------------

        recent_memories = session.exec(
            select(Memory)
            .where(
                Memory.workspace_id == resolved_workspace_id,
                Memory.chat_id == chat_id,
            )
            .order_by(Memory.created_at.desc())
            .limit(10)
        ).all()

        for m in recent_memories:

            if m.id == memory.id:
                continue

            if memory.memory_type == "task" and m.memory_type == "event":

                relationship = MemoryRelationship(
                    workspace_id=resolved_workspace_id,
                    source_memory_id=memory.id,
                    target_memory_id=m.id,
                    relationship_type="triggered_by"
                )

                session.add(relationship)

            if memory.memory_type == "decision" and m.memory_type == "task":

                relationship = MemoryRelationship(
                    workspace_id=resolved_workspace_id,
                    source_memory_id=memory.id,
                    target_memory_id=m.id,
                    relationship_type="resolves"
                )

                session.add(relationship)

        session.commit()

        # -----------------------------
        # VECTOR GRAPH RELATIONSHIPS
        # -----------------------------

        create_vector_relationships(memory)

        # -----------------------------
        # Generate insights
        # -----------------------------

        generate_insights(
            chat_id,
            resolved_workspace_id,
        )

        return memory

    finally:

        session.close()
