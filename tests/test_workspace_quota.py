from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_workspace_quota_blocks_events():

    client.post(
        "/workspaces",
        json={
            "id": "quota-test",
            "name": "Quota Test"
        }
    )

    client.post(
        "/workspace/context",
        json={
            "workspace": "quota-test"
        }
    )

    client.post(
        "/workspace/quotas/quota-test",
        json={
            "maxEvents": 1
        }
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

    assert (
        first.json()[
            "event"
        ][
            "status"
        ]
        ==
        "received"
    )

    assert (
        second.json()[
            "event"
        ][
            "status"
        ]
        ==
        "blocked"
    )