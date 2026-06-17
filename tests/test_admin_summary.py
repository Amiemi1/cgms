from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_admin_summary():

    response = client.get(
        "/admin/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["platform"] == "CGMS"
    assert "workspaces" in data
    assert "connectors" in data
    assert data["ready"] is True


def test_product_console():

    response = client.get(
        "/product/console"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product"] == "CGMS"
    assert data["readinessScore"] >= 90


def test_release_status():

    response = client.get(
        "/release/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "candidate"
    assert "next" in data