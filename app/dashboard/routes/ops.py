from datetime import datetime

from fastapi import APIRouter

from app.services.workspace.registry import (
    get_workspaces
)

from app.services.connectors.registry import (
    get_connectors
)

from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS
)

from datetime import datetime

router = APIRouter()


BOOT_TIME = datetime.utcnow()

OPS_ERRORS = []


@router.get(
    "/ops/health"
)
def ops_health():

    connectors = get_connectors()

    connected = len([

        x

        for x

        in connectors.values()

        if x.get(
            "enabled"
        )

    ])

    return {

        "status":
            "healthy",

        "uptimeSeconds":

            int(
                (
                    datetime.utcnow()
                    -
                    BOOT_TIME
                ).total_seconds()
            ),

        "workspaces":

            len(
                get_workspaces()
            ),

        "connectors":

            connected,

        "events":

            len(
                INGESTED_EVENTS
            ),

        "timestamp":

            datetime.utcnow()
            .isoformat()
    }

@router.get(
    "/ops/events"
)
def ops_events(
    limit: int = 50
):

    return {

        "count":
            min(
                limit,
                len(
                    INGESTED_EVENTS
                )
            ),

        "events":
            INGESTED_EVENTS[
                :limit
            ],

        "source":
            "ingested_events"
    }

@router.get(
    "/ops/latency"
)
def ops_latency():

    if not INGESTED_EVENTS:

        return {

            "healthy":
                True,

            "events":
                0,

            "lastEventLatencyMs":
                None,

            "averageLatencyMs":
                None
        }

    now = datetime.utcnow()

    latencies = []

    for event in INGESTED_EVENTS:

        try:

            ts = datetime.fromisoformat(
                event[
                    "receivedAt"
                ]
            )

            latency = (

                now
                -
                ts

            ).total_seconds() * 1000

            latencies.append(
                round(
                    latency,
                    2
                )
            )

        except Exception:

            pass

    return {

        "healthy":
            True,

        "events":
            len(
                latencies
            ),

        "lastEventLatencyMs":

            latencies[
                0
            ]

            if latencies

            else None,

        "averageLatencyMs":

            round(

                sum(
                    latencies
                )

                /

                len(
                    latencies
                ),

                2
            )

            if latencies

            else None
    }

@router.post("/ops/errors")
def record_error(payload: dict):

    error = {
        "message": payload.get("message", "unknown_error"),
        "source": payload.get("source", "runtime"),
        "severity": payload.get("severity", "medium"),
        "timestamp": datetime.utcnow().isoformat()
    }

    OPS_ERRORS.insert(0, error)

    del OPS_ERRORS[100:]

    return {
        "ok": True,
        "error": error
    }


@router.get("/ops/errors")
def ops_errors(limit: int = 50):

    return {
        "count": min(limit, len(OPS_ERRORS)),
        "errors": OPS_ERRORS[:limit],
        "healthy": len(OPS_ERRORS) == 0
    }