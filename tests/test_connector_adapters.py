from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_slack_adapter():

    response = client.post(
        "/adapters/slack",
        json={
            "text": "Distributor strategy review",
            "channel": "commercial"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["adapter"] == "slack"
    assert "event" in data


def test_teams_adapter():

    response = client.post(
        "/adapters/teams",
        json={
            "text": "Teams event"
        }
    )

    assert response.status_code == 200

    assert response.json()["adapter"] == "teams"


def test_gmail_adapter():

    response = client.post(
        "/adapters/gmail",
        json={
            "subject": "Gmail event"
        }
    )

    assert response.status_code == 200

    assert response.json()["adapter"] == "gmail"


def test_calendar_adapter():

    response = client.post(
        "/adapters/calendar",
        json={
            "title": "Calendar event"
        }
    )

    assert response.status_code == 200

    assert response.json()["adapter"] == "calendar"