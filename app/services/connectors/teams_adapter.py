from app.services.connectors.event_ingestion import (
    ingest_external_event
)


def process_teams_event(
    payload: dict,
    workspace_id: str,
    quota_repository=None,
):

    return {

        "adapter":
            "teams",

        "event":

            ingest_external_event(

                "teams",

                payload,

                workspace_id,

                quota_repository,
            )
    }
