from fastapi import APIRouter

from app.services.connectors.event_ingestion import (
    ingest_external_event,
    get_ingested_events
)


router = APIRouter()


@router.post("/ingest/{source}")
def ingest(
    source: str,
    payload: dict
):

    return {
        "ok": True,
        "event":
            ingest_external_event(
                source,
                payload
            )
    }


@router.get("/ingest/events")
def events(
    limit: int = 100
):

    return {
        "events":
            get_ingested_events(
                limit
            )
    }