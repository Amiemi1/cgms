from app.services.connectors.event_ingestion import (
    ingest_external_event
)


def process_gmail_event(
    payload: dict
):

    return {

        "adapter":
            "gmail",

        "event":

            ingest_external_event(

                "gmail",

                payload
            )
    }