from datetime import datetime

from fastapi import APIRouter

from app.dashboard.routes.ops import (
    OPS_ERRORS
)

from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS
)


router = APIRouter()

STARTED = datetime.utcnow()


@router.get("/ops/runtime")
def runtime():

    timeline = []

    timeline.append({

        "type":
            "startup",

        "timestamp":
            STARTED.isoformat(),

        "message":
            "CGMS started"
    })

    for event in INGESTED_EVENTS:

        timeline.append({

            "type":
                "event",

            "timestamp":
                event.get(
                    "receivedAt"
                ),

            "message":
                event.get(
                    "source",
                    "unknown"
                )
        })

    for error in OPS_ERRORS:

        timeline.append({

            "type":
                "error",

            "timestamp":
                error.get(
                    "timestamp"
                ),

            "message":
                error.get(
                    "message"
                )
        })

    timeline.sort(
        key=lambda x:
            x["timestamp"]
    )

    return {

        "entries":
            len(
                timeline
            ),

        "timeline":
            timeline
    }