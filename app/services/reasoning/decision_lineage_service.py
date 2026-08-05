from app.db.models.decision_lineage import DecisionLineage
from app.db.models.memory import Memory
from app.services.workspace.tenant_scope import (
    inherit_workspace_id,
    load_scoped_record,
    normalize_workspace_id,
)


def record_decision_lineage(
    session,
    decision_id,
    source_memory_id=None,
    reasoning_engine=None,
    triggered_by_user=None,
    *,
    workspace_id: str,
):
    resolved_workspace_id = normalize_workspace_id(workspace_id)
    decision = load_scoped_record(
        session,
        Memory,
        decision_id,
        resolved_workspace_id,
    )

    if decision is None:
        return None

    if source_memory_id is not None:
        source_memory = load_scoped_record(
            session,
            Memory,
            source_memory_id,
            resolved_workspace_id,
        )

        if source_memory is None:
            return None

    lineage = DecisionLineage(
        workspace_id=inherit_workspace_id(decision),
        decision_id=decision_id,
        source_memory_id=source_memory_id,
        reasoning_engine=reasoning_engine,
        triggered_by_user=triggered_by_user
    )

    session.add(lineage)
    session.commit()

    return lineage
