from fastapi.testclient import TestClient

from app.dashboard.main import app


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


def test_workspace_context():

    response = client.post(

        "/workspace/context",

        json={

            "workspace":
                "test"
        }
    )

    assert (
        response.status_code
        ==
        200
    )

    assert (
        response.json()["id"]
        ==
        "test"
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
        "test"
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
        "test"
        in metrics
    )