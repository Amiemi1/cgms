from fastapi.testclient import TestClient
from app.dashboard.main import app


client = TestClient(app)


def test_enterprise_readiness():

    response = client.get(
        "/enterprise/readiness"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["system"] == "CGMS"

    assert (
        data["enterpriseReadinessScore"]
        >= 90
    )

    assert (
        data["modules"]["rbac"]
        == "ready"
    )