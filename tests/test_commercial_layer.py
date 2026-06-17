from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_usage_endpoint():

    response = client.get(
        "/commercial/usage"
    )

    assert response.status_code == 200

    data = response.json()

    assert "usage" in data


def test_plan_switch():

    response = client.post(

        "/commercial/plan",

        json={

            "plan":
                "team"
        }
    )

    assert (
        response.status_code
        ==
        200
    )

    assert (
        response.json()[
            "plan"
        ]
        ==
        "team"
    )


def test_enforcement():

    response = client.get(
        "/commercial/enforcement"
    )

    assert (
        response.status_code
        ==
        200
    )

    assert (
        "allowed"
        in
        response.json()
    )