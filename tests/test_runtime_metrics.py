from fastapi.testclient import TestClient
from app.dashboard.main import app

client = TestClient(app)


def test_runtime_metrics_endpoint():

    response = client.get("/runtime/metrics")

    assert response.status_code == 200

    data = response.json()

    assert data["runtimeHealth"] == 100
    assert data["autonomyScore"] >= 90
    assert "timestamp" in data