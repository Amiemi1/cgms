from app.db.models.decision_lineage import DecisionLineage


def record_decision_lineage(
    session,
    decision_id,
    source_memory_id=None,
    reasoning_engine=None,
    triggered_by_user=None
):

    lineage = DecisionLineage(
        decision_id=decision_id,
        source_memory_id=source_memory_id,
        reasoning_engine=reasoning_engine,
        triggered_by_user=triggered_by_user
    )

    session.add(lineage)
    session.commit()

    return lineage