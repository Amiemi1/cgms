from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(
    app
)


def test_external_ingestion():

    payload = {

        "text":
            "Prepare distributor strategy pack",

        "user":
            "Murphy"
    }

    response = client.post(

        "/ingest/slack",

        json=payload
    )

    assert (
        response.status_code
        ==
        200
    )

    body = response.json()

    assert (
        body["ok"]
        is True
    )

    assert (
        body["event"]["source"]
        ==
        "slack"
    )

    assert (
        body["event"]["orchestrated"]
        is True
    )


def test_ingestion_history():

    response = client.get(
        "/ingest/events"
    )

    assert (
        response.status_code
        ==
        200
    )

    data = response.json()

    assert (
        "events"
        in data
    )

    assert (
        isinstance(
            data["events"],
            list
        )
    )