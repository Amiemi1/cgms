from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_ops_health():

    response = client.get("/ops/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert "uptimeSeconds" in data
    assert "workspaces" in data


def test_ops_events():

    response = client.get("/ops/events")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "events" in data


def test_ops_latency():

    response = client.get("/ops/latency")

    assert response.status_code == 200

    data = response.json()

    assert data["healthy"] is True
    assert "events" in data


def test_ops_errors():

    client.post(
        "/ops/errors",
        json={
            "message": "test error",
            "source": "test",
            "severity": "low"
        }
    )

    response = client.get("/ops/errors")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "errors" in data

def test_ops_runtime():

    response = client.get("/ops/runtime")

    assert response.status_code == 200

    data = response.json()

    assert "entries" in data
    assert "timeline" in data
    assert isinstance(data["timeline"], list)