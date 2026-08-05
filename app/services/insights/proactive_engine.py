from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.insight import Insight
from app.db.models.memory_relationship import MemoryRelationship
from app.services.workspace.tenant_scope import normalize_workspace_id


def generate_insights(
    chat_id: int,
    workspace_id: str,
):

    session = SessionLocal()

    insights = []
    resolved_workspace_id = normalize_workspace_id(workspace_id)

    try:

        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id == resolved_workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        for memory in memories:

            # --------------------------------------------------
            # Find relationships connected to this memory
            # --------------------------------------------------

            relations = session.exec(
                select(MemoryRelationship).where(
                    MemoryRelationship.workspace_id
                    == resolved_workspace_id,
                    MemoryRelationship.source_memory_id
                    == memory.id,
                )
            ).all()

            if relations:

                insights.append(
                    f"'{memory.summary}' is connected to {len(relations)} other memories."
                )

        # --------------------------------------------------
        # Save insights
        # --------------------------------------------------

        for text in insights:

            insight = Insight(
                workspace_id=resolved_workspace_id,
                chat_id=chat_id,
                message=text,
                insight_type="auto"
            )

            session.add(insight)

        session.commit()

        return insights

    finally:

        session.close()
