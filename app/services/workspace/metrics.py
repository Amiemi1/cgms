from app.services.workspace.registry import (
    get_workspaces
)

from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS
)


def workspace_metrics():

    workspaces = get_workspaces()

    result = {}

    for ws in workspaces:

        events = [

            e

            for e

            in INGESTED_EVENTS

            if (

                e.get(
                    "workspace"
                )

                ==

                ws
            )
        ]

        result[
            ws
        ] = {

            "events":
                len(
                    events
                ),

            "orchestrated":
                len(

                    [

                        e

                        for e

                        in events

                        if (

                            e.get(
                                "orchestrated"
                            )

                        )

                    ]

                ),

            "health":

                100

                if

                events

                else

                95
        }

    return result