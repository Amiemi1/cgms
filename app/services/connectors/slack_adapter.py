from app.services.connectors.event_ingestion import (
    ingest_external_event
)


def process_slack_event(
    payload: dict
):

    event = ingest_external_event(

        "slack",

        payload
    )

    return {

        "adapter":
            "slack",

        "accepted":
            event.get(
                "status"
            )

            !=

            "blocked",

        "event":
            event
    }