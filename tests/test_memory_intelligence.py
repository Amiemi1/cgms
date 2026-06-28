from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_memory_intelligence_not_found():

    response = client.get(
        "/memory/intelligence/999999"
    )

    assert response.status_code == 404


def test_memory_event_missing_id():

    response = client.post(
        "/memory/event",
        json={
            "event": "MemoryUpdated"
        }
    )

    assert response.status_code == 200
    assert response.json()["processed"] is False
    assert response.json()["reason"] == "missing_memory_id"


def test_memory_score_cache_missing():

    response = client.get(
        "/memory/score-cache/999999"
    )

    assert response.status_code == 200
    assert response.json()["cached"] is False


def test_memory_dashboard():

    response = client.get(
        "/memory/dashboard"
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_memories" in data
    assert "average_composite" in data
    assert "top_memories" in data