from fastapi import APIRouter, Depends
from sqlmodel import select

from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship
from app.db.session import SessionLocal
from app.services.auth.application_authorization import (
    enforce_application_authorization,
)
from app.services.workspace.tenant_scope import get_current_workspace_id


router = APIRouter(
    prefix="/memory-graph",
    tags=["Memory Graph"],
)


def _get_workspace_id(
    principal=Depends(
        enforce_application_authorization
    ),
) -> str:
    return get_current_workspace_id(principal)



@router.get("/{chat_id}")
def get_memory_graph(
    chat_id: int,
    workspace_id: str = Depends(
        _get_workspace_id
    ),
):

    session = SessionLocal()

    try:

        memories = session.exec(
            select(Memory).where(
                Memory.workspace_id == workspace_id,
                Memory.chat_id == chat_id,
            )
        ).all()

        relationships = session.exec(
            select(MemoryRelationship).where(
                MemoryRelationship.workspace_id == workspace_id
            )
        ).all()

        nodes = []
        edges = []

        # ------------------------------------------------
        # NODE IMPORTANCE CALCULATION
        # ------------------------------------------------

        dependency_count = {}

        for rel in relationships:

            dependency_count[rel.source_memory_id] = (
                dependency_count.get(rel.source_memory_id, 0) + 1
            )

            dependency_count[rel.target_memory_id] = (
                dependency_count.get(rel.target_memory_id, 0) + 1
            )

        # ------------------------------------------------
        # BUILD NODES
        # ------------------------------------------------

        for m in memories:

            importance = dependency_count.get(m.id, 0)

            risk = None

            # tasks without decision
            if m.memory_type == "task":

                has_decision = any(
                    r.target_memory_id == m.id and r.relationship_type == "resolves"
                    for r in relationships
                )

                if not has_decision:
                    risk = "blocked"

            # events without tasks
            if m.memory_type == "event":

                has_tasks = any(
                    r.target_memory_id == m.id and r.relationship_type == "triggered_by"
                    for r in relationships
                )

                if not has_tasks:
                    risk = "at_risk"

            nodes.append({

                "id": m.id,
                "label": m.summary,
                "type": m.memory_type,
                "importance": importance,
                "risk": risk

            })

        # ------------------------------------------------
        # BUILD EDGES
        # ------------------------------------------------

        for r in relationships:

            edges.append({

                "source": r.source_memory_id,
                "target": r.target_memory_id,
                "type": r.relationship_type

            })

        return {

            "nodes": nodes,
            "edges": edges

        }

    finally:

        session.close()
