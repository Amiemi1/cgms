from fastapi.testclient import TestClient

from app.dashboard.main import app
from app.services.workspace.context import (
    get_workspace,
)


client = TestClient(
    app
)


def test_workspace_creation():

    response = client.post(

        "/workspaces",

        json={

            "id":
                "test",

            "name":
                "Test Workspace",

            "createdBy":
                "test"
        }
    )

    assert (
        response.status_code
        ==
        200
    )

    data = response.json()

    assert (
        data["name"]
        ==
        "Test Workspace"
    )


def test_legacy_connector_workspace_is_governed_default():

    assert (
        get_workspace()
        ==
        {
            "id": "default"
        }
    )


def test_workspace_ingestion():

    response = client.post(

        "/ingest/slack",

        json={

            "text":
                "workspace event"
        }
    )

    assert (
        response.status_code
        ==
        200
    )

    event = response.json()["event"]

    assert (
        event["workspace"]
        ==
        "default"
    )


def test_workspace_metrics():

    response = client.get(
        "/workspace/metrics"
    )

    assert (
        response.status_code
        ==
        200
    )

    metrics = response.json()

    assert (
        "default"
        in metrics
    )
