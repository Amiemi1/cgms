from fastapi.testclient import TestClient

import app.services.connectors.event_ingestion as event_ingestion
from app.dashboard.main import app


client = TestClient(app)


def test_workspace_quota_blocks_events(
    monkeypatch,
):

    monkeypatch.setattr(
        event_ingestion,
        "INGESTED_EVENTS",
        [],
    )

    quota_response = client.post(
        "/workspace/quotas/default",
        json={
            "maxEvents": 1
        },
    )

    assert (
        quota_response.status_code
        ==
        200
    )

    first = client.post(
        "/ingest/slack",
        json={
            "text": "event one"
        }
    )

    second = client.post(
        "/ingest/slack",
        json={
            "text": "event two"
        }
    )

    first_event = first.json()[
        "event"
    ]

    second_event = second.json()[
        "event"
    ]

    assert (
        first_event["workspace"]
        ==
        "default"
    )

    assert (
        second_event["workspace"]
        ==
        "default"
    )

    assert (
        first_event["status"]
        ==
        "received"
    )

    assert (
        second_event["status"]
        ==
        "blocked"
    )
