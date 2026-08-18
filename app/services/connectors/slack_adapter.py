from app.services.connectors.event_ingestion import (
    ingest_external_event
)


def process_slack_event(
    payload: dict,
    workspace_id: str,
    quota_repository=None,
):

    event = ingest_external_event(

        "slack",

        payload,

        workspace_id,

        quota_repository,
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
