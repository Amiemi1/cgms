from app.services.connectors.event_ingestion import (
    ingest_external_event
)


def process_calendar_event(
    payload: dict,
    workspace_id: str,
    quota_repository=None,
):

    return {

        "adapter":
            "calendar",

        "event":

            ingest_external_event(

                "calendar",

                payload,

                workspace_id,

                quota_repository,
            )
    }
