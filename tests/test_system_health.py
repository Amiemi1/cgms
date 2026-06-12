from fastapi.testclient import TestClient
from app.dashboard.main import app

client = TestClient(app)


def test_system_health_endpoint():

    response = client.get(
        "/system/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["system"] == "CGMS"
    assert data["status"] == "healthy"
    assert "subsystems" in data
    assert "runtime" in data