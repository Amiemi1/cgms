from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_product_readiness_assessment_endpoint() -> None:
    response = client.get("/product-readiness/assessment")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_product_readiness_capabilities_endpoint() -> None:
    response = client.get("/product-readiness/capabilities")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_unknown_product_capability_returns_404() -> None:
    response = client.get(
        "/product-readiness/capabilities/non-existent-capability"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            "Capability 'non-existent-capability' not found."
        )
    }


def test_product_readiness_recommendations_endpoint() -> None:
    response = client.get("/product-readiness/recommendations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_product_readiness_categories_endpoint() -> None:
    response = client.get("/product-readiness/categories")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_existing_enterprise_readiness_endpoint_is_preserved() -> None:
    response = client.get("/enterprise/readiness")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)