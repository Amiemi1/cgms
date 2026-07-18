from fastapi.testclient import TestClient

from app.dashboard.main import app


client = TestClient(app)


def test_product_readiness_dashboard_returns_html() -> None:
    response = client.get("/product-readiness/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_product_readiness_dashboard_contains_expected_title() -> None:
    response = client.get("/product-readiness/dashboard")

    assert "CGMS Product Readiness" in response.text
    assert "Capability Register" in response.text
    assert "Engineering Recommendations" in response.text


def test_product_readiness_dashboard_uses_dynamic_api_endpoints() -> None:
    response = client.get("/product-readiness/dashboard")

    expected_endpoints = [
        "/product-readiness/assessment",
        "/product-readiness/capabilities",
        "/product-readiness/recommendations",
        "/product-readiness/categories",
    ]

    for endpoint in expected_endpoints:
        assert endpoint in response.text


def test_legacy_product_console_remains_available() -> None:
    response = client.get("/product/console")

    assert response.status_code == 200
    assert response.json()["product"] == "CGMS"


def test_existing_product_readiness_api_remains_available() -> None:
    response = client.get("/product-readiness/assessment")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)
def test_dashboard_recognizes_production_ready_status() -> None:
    response = client.get("/product-readiness/dashboard")

    assert response.status_code == 200
    assert '"production_ready"' in response.text
    assert "Production-Ready Capabilities" in response.text


def test_dashboard_displays_recommendation_reason() -> None:
    response = client.get("/product-readiness/dashboard")

    assert response.status_code == 200
    assert "recommendation.reason" in response.text