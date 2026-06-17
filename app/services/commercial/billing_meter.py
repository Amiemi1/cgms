from app.services.connectors.event_ingestion import (
    INGESTED_EVENTS
)

from app.services.workspace.registry import (
    get_workspaces
)


def usage_meter():

    workspaces = get_workspaces()

    result = {}

    total = 0

    for workspace in workspaces:

        count = len([

            e

            for e

            in INGESTED_EVENTS

            if (

                e.get(
                    "workspace"
                )

                ==

                workspace
            )
        ])

        total += count

        result[
            workspace
        ] = {

            "events":
                count,

            "estimatedUnits":

                max(
                    1,
                    count
                ),

            "estimatedCost":

                round(

                    count

                    *

                    0.05,

                    2
                )
        }

    return {

        "usage":

            result,

        "totalEvents":

            total
    }