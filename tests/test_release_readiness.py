from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_release_status():

    response = client.get(
        "/release/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["status"]
        ==
        "candidate"
    )


def test_release_narrative():

    response = client.get(
        "/release/narrative"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["product"]
        ==
        "CGMS"
    )

    assert (
        data["stage"]
        ==
        "release_candidate"
    )