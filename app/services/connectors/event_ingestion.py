from datetime import datetime

from app.services.orchestration.event_router import (
    route_memory_update
)

from app.services.workspace.context import (
    get_workspace
)

from app.services.workspace.quotas import (
    get_workspace_quota
)

INGESTED_EVENTS = []


def ingest_external_event(
    source: str,
    payload: dict
):

    record = {

        "workspace":
            get_workspace()[
                "id"
            ],

        "source":
            source,

        "payload":
            payload,

        "status":
            "received",

        "receivedAt":
            datetime.utcnow()
            .isoformat()
    }


    quota = enforce_event_quota(
        record[
            "workspace"
        ]
    )

    if not quota[
        "allowed"
    ]:

        record[
            "status"
        ] = "blocked"

        record[
            "quota"
        ] = quota

        return record

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

    workspace = get_workspace()[
        "id"
    ]

    return [

        event

        for event

        in INGESTED_EVENTS

        if (
            event.get(
                "workspace"
            )
            ==
            workspace
        )

    ][
        :limit
    ]

def enforce_event_quota(
    workspace_id: str
):

    quota = get_workspace_quota(
        workspace_id
    )

    count = len([

        event for event in INGESTED_EVENTS

        if event.get("workspace") == workspace_id
    ])

    return {
        "allowed": count < quota["maxEvents"],
        "usage": count,
        "limit": quota["maxEvents"]
    }