from fastapi.testclient import TestClient
from app.dashboard.main import app

client = TestClient(app)


def test_environment_manifest_endpoint():

    response = client.get(
        "/system/environment"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["system"] == "CGMS"
    assert "environment" in data
    assert "deployment" in data
    assert data["deployment"]["ready"] is True