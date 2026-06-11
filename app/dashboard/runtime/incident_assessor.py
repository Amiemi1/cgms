# app/dashboard/runtime/incident_assessor.py

from datetime import datetime


def assess_runtime_impact(event):

    payload = event.get("payload", {})

    total = payload.get("total", 0)
    health = payload.get("healthScore", 100)
    duplicates = payload.get("duplicateCandidates", 0)

    severity = "healthy"

    if health < 50:
        severity = "critical"

    elif health < 75:
        severity = "warning"

    elif duplicates > 3:
        severity = "degraded"

    impact = {
        "severity": severity,
        "healthScore": health,
        "duplicates": duplicates,
        "affectedSubsystem":
            "memory_runtime",

        "recoveryRequired":
            severity != "healthy",

        "timestamp":
            datetime.utcnow().isoformat()
    }

    print("🚨 INCIDENT ASSESSMENT", impact)

    return impact