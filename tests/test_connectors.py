from fastapi.testclient import TestClient
from app.dashboard.main import app


client = TestClient(app)


def test_connectors_endpoint():

    response = client.get(
        "/connectors"
    )

    assert response.status_code == 200

    data = response.json()

    assert "slack" in data
    assert "teams" in data
    assert "gmail" in data
    assert "calendar" in data

    assert isinstance(
        data["slack"]["enabled"],
        bool
    )

    assert data["slack"]["status"] in [
        "not_connected",
        "connected"
    ]