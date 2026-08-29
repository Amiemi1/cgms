from datetime import datetime

from app.services.explainability.audit_store import (
    store_audit_record
)


def explain_runtime_decision(
    event_name: str,
    payload: dict,
    *,
    workspace_id: str | None = None,
    actor_id: str | None = None,
    correlation_id: str | None = None,
):

    impact = payload.get("impact", {})

    explanation = {
        "event": event_name,
        "reason": "Runtime event processed through orchestration loop",
        "severity": impact.get("severity", "unknown"),
        "affectedSubsystem": impact.get("affectedSubsystem", "unknown"),
        "recoveryRequired": impact.get("recoveryRequired", False),
        "decision": "monitor" if not impact.get("recoveryRequired") else "escalate",
        "timestamp": datetime.utcnow().isoformat()
    }

    store_audit_record(
        explanation,
        workspace_id=workspace_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
    )

    print(
        "🧾 EXPLAINABILITY RECORD",
        explanation
    )

    return explanation
