from datetime import datetime

from app.services.explainability.audit_store import (
    store_audit_record
)


def explain_runtime_decision(event_name: str, payload: dict):

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
        explanation
    )

    print(
        "🧾 EXPLAINABILITY RECORD",
        explanation
    )

    return explanation