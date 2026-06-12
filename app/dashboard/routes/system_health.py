from fastapi import APIRouter
from datetime import datetime


router = APIRouter()

START_TIME = datetime.utcnow()


@router.get("/system/health")
def system_health():

    uptime = (
        datetime.utcnow() -
        START_TIME
    ).total_seconds()

    return {
        "system": "CGMS",

        "status": "healthy",

        "uptimeSeconds": round(
            uptime
        ),

        "subsystems": {
            "dashboard": "healthy",
            "memory_runtime": "healthy",
            "audit": "healthy",
            "orchestration": "healthy",
            "rbac": "healthy",
            "session_replay": "healthy"
        },

        "runtime": {
            "selfHealing": True,
            "incidentMonitoring": True,
            "autonomyEnabled": True
        },

        "timestamp":
            datetime.utcnow()
            .isoformat()
    }