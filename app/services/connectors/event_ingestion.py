from datetime import datetime

from app.services.orchestration.event_router import (
    route_memory_update
)


INGESTED_EVENTS = []


def ingest_external_event(
    source: str,
    payload: dict
):

    record = {
        "source": source,
        "payload": payload,
        "status": "received",
        "receivedAt":
            datetime.utcnow()
            .isoformat()
    }

    INGESTED_EVENTS.insert(
        0,
        record
    )

    del INGESTED_EVENTS[300:]

    try:

        route_memory_update({

            "source":
                source,

            "external":
                True,

            "payload":
                payload
        })

        record[
            "orchestrated"
        ] = True

    except Exception as e:

        record[
            "orchestrated"
        ] = False

        record[
            "error"
        ] = str(
            e
        )


    print(
        "📥 EXTERNAL EVENT INGESTED",
        record
    )

    return record


def get_ingested_events(
    limit: int = 100
):

    return INGESTED_EVENTS[:limit]