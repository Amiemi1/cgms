from fastapi.testclient import TestClient

from app.dashboard.main import app
from app.services.product_readiness.assessment import assess_product
from app.services.product_readiness.bootstrap import (
    bootstrap_product_capabilities,
)
from app.services.product_readiness.registry import (
    clear,
    get,
    list_all,
)


def setup_function() -> None:
    clear()


def teardown_function() -> None:
    clear()


def test_bootstrap_loads_authoritative_catalogue() -> None:
    loaded_count = bootstrap_product_capabilities()

    assert loaded_count == 38
    assert len(list_all()) == 38
    assert get("CAP-001") is not None
    assert get("CAP-038") is not None


def test_bootstrap_is_idempotent() -> None:
    first_count = bootstrap_product_capabilities()
    first_ids = [
        capability.id
        for capability in list_all()
    ]

    second_count = bootstrap_product_capabilities()
    second_ids = [
        capability.id
        for capability in list_all()
    ]

    assert first_count == 38
    assert second_count == 38
    assert first_ids == second_ids
    assert len(second_ids) == len(set(second_ids))


def test_bootstrap_produces_non_empty_assessment() -> None:
    bootstrap_product_capabilities()

    assessment = assess_product()

    assert assessment.total_capabilities == 38
    assert assessment.overall_score > 0
    assert assessment.category_scores
    assert assessment.implemented > 0
    assert assessment.in_progress > 0
    assert assessment.not_started > 0


def test_bootstrap_preserves_priority_and_scope_metadata() -> None:
    bootstrap_product_capabilities()

    secure_authentication = get("CAP-001")
    workspace_isolation = get("CAP-003")
    organizational_memory = get("CAP-006")
    connector_marketplace = get("CAP-038")

    assert secure_authentication is not None
    assert secure_authentication.priority.value == "P0"
    assert secure_authentication.required_for_mlp is True
    assert secure_authentication.required_for_pilot is True

    assert workspace_isolation is not None
    assert workspace_isolation.status.value == "pilot_ready"
    assert workspace_isolation.tests_passing is True
    assert workspace_isolation.security_reviewed is True
    assert workspace_isolation.ux_complete is True
    assert workspace_isolation.documented is True

    assert organizational_memory is not None
    assert organizational_memory.status.value == "implemented"
    assert organizational_memory.tests_passing is True

    assert connector_marketplace is not None
    assert connector_marketplace.priority.value == "P4"
    assert connector_marketplace.status.value == "not_started"


def test_application_startup_bootstraps_capabilities() -> None:
    clear()

    with TestClient(app) as client:
        response = client.get(
            "/product-readiness/assessment"
        )

        assert response.status_code == 200
        assert response.json()["total_capabilities"] == 38
