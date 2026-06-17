from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(
    app
)


def test_workspace_persistence():

    response = client.post(

        "/workspaces",

        json={

            "id":
                "persist-test",

            "name":
                "Persistence Test",

            "createdBy":
                "test"
        }
    )

    assert (
        response.status_code
        ==
        200
    )

    workspaces = client.get(
        "/workspaces"
    )

    data = workspaces.json()

    assert (
        "persist-test"
        in data
    )


def test_connector_persistence():

    client.post(
        "/connectors/slack/activate"
    )

    response = client.get(
        "/connectors"
    )

    data = response.json()

    assert (

        data[
            "slack"
        ][
            "enabled"
        ]

        is True
    )


def test_connector_health():

    response = client.get(
        "/connectors/health"
    )

    assert (
        response.status_code
        ==
        200
    )

    assert (
        "slack"
        in
        response.json()
    )