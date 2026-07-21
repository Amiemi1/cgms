from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.main import app as production_app
from app.dashboard.routes.patent_readiness_dashboard import (
    get_patent_dashboard_service,
    router as patent_dashboard_router,
)
from app.services.auth.jwt_handler import (
    create_access_token,
)
from app.services.patent_governance.dashboard_service import (
    PatentDashboardService,
)
from app.services.patent_governance.evidence_registry import (
    PatentEvidenceRegistry,
)
from app.services.patent_governance.innovation_registry import (
    PatentInnovationRegistry,
)
from app.services.patent_governance.registry import (
    PatentGovernanceRegistry,
)


TEST_JWT_SECRET = (
    "cgms-test-secret-key-with-more-than-32-characters"
)


@pytest.fixture(autouse=True)
def configure_test_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Configure a deterministic test-only JWT environment.

    No production or local development secret is used.
    """
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        TEST_JWT_SECRET,
    )

    monkeypatch.setenv(
        "CGMS_JWT_EXPIRE_MINUTES",
        "60",
    )

    monkeypatch.setenv(
        "CGMS_JWT_ISSUER",
        "cgms-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-dashboard-test",
    )


def build_service() -> PatentDashboardService:
    governance_registry = PatentGovernanceRegistry()

    evidence_registry = PatentEvidenceRegistry(
        governance_registry
    )

    innovation_registry = PatentInnovationRegistry(
        governance_registry,
        evidence_registry,
    )

    return PatentDashboardService(
        governance_registry=governance_registry,
        evidence_registry=evidence_registry,
        innovation_registry=innovation_registry,
    )


def build_isolated_client() -> TestClient:
    isolated_app = FastAPI()

    service = build_service()

    isolated_app.dependency_overrides[
        get_patent_dashboard_service
    ] = lambda: service

    isolated_app.include_router(
        patent_dashboard_router
    )

    return TestClient(isolated_app)


def create_test_token(
    role: str,
    *,
    user_id: str = "test-user-001",
    expires_delta: timedelta | None = None,
) -> str:
    return create_access_token(
        {
            "user_id": user_id,
            "role": role,
        },
        expires_delta=expires_delta,
    )


def bearer_headers(
    token: str,
    **additional_headers: str,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {token}",
    }

    headers.update(additional_headers)

    return headers


def test_dashboard_view_masks_sensitive_identifiers() -> None:
    service = build_service()

    dashboard = service.build_view(
        include_sensitive=False
    )

    filing = dashboard["filing"]

    assert filing["application_number"] == "••••7873"
    assert filing["confirmation_number"] == "••••"
    assert filing["customer_number"] == "••••5429"
    assert filing["patent_center_number"] == "••••3697"
    assert filing["identifiers_masked"] is True

    serialized = str(dashboard)

    assert "63/987,873" not in serialized
    assert "225429" not in serialized
    assert "74563697" not in serialized


def test_authorized_service_view_can_include_identifiers() -> None:
    service = build_service()

    dashboard = service.build_view(
        include_sensitive=True
    )

    filing = dashboard["filing"]

    assert filing["application_number"] == "63/987,873"
    assert filing["confirmation_number"] == "8158"
    assert filing["customer_number"] == "225429"
    assert filing["patent_center_number"] == "74563697"
    assert filing["identifiers_masked"] is False


def test_dashboard_reports_expected_governance_metrics() -> None:
    service = build_service()

    dashboard = service.build_view()

    assert dashboard["metrics"]["administrative"] == {
        "completed": 4,
        "total": 5,
        "percent": 80,
    }

    assert dashboard["metrics"]["evidence"] == {
        "verified": 4,
        "partially_verified": 13,
        "total": 17,
        "percent": 24,
    }

    assert dashboard["metrics"]["innovations"] == {
        "total": 9,
        "deployed": 3,
        "implemented": 4,
        "in_progress": 2,
    }

    assert dashboard["metrics"]["legal_review"] == {
        "reviewed": 0,
        "total": 6,
        "percent": 0,
    }

    assert dashboard["metrics"]["coverage"] == {
        "assessed": 0,
        "total": 9,
        "percent": 0,
    }


def test_dashboard_generates_governance_actions() -> None:
    service = build_service()

    dashboard = service.build_view()

    action_ids = {
        action["id"]
        for action in dashboard["actions"]
    }

    assert action_ids == {
        "ACT-MIL-CGMS-003",
        "ACT-MIL-CGMS-004",
        "ACT-MIL-CGMS-005",
        "ACT-EVIDENCE-REVIEW",
        "ACT-LEGAL-REVIEW",
        "ACT-COVERAGE-ASSESSMENT",
    }

    priorities = [
        action["priority"]
        for action in dashboard["actions"]
    ]

    assert priorities[:3] == [
        "High",
        "High",
        "High",
    ]

    legal_action = next(
        action
        for action in dashboard["actions"]
        if action["id"] == "ACT-LEGAL-REVIEW"
    )

    assert (
        "6 technical claim candidates"
        in legal_action["description"]
    )


def test_dashboard_preserves_legal_and_coverage_controls() -> None:
    service = build_service()

    dashboard = service.build_view()

    assert dashboard["page"]["confidential"] is True

    assert (
        dashboard["page"]["production_access_enabled"]
        is False
    )

    assert (
        "not legal advice"
        in dashboard["governance"]["legal_disclaimer"]
    )

    assert (
        "not an official USPTO status system"
        in dashboard["governance"]["legal_disclaimer"]
    )

    assert (
        "Coverage remains unassessed"
        in dashboard["governance"]["coverage_notice"]
    )

    assert all(
        candidate["legal_review_status"]
        == "Not Reviewed"
        for candidate in dashboard["claim_candidates"]
    )


def test_dashboard_bootstrap_is_repeatable() -> None:
    service = build_service()

    first_dashboard = service.build_view()
    second_dashboard = service.build_view()

    assert len(first_dashboard["timeline"]) == 5
    assert len(second_dashboard["timeline"]) == 5

    assert len(first_dashboard["evidence"]) == 17
    assert len(second_dashboard["evidence"]) == 17

    assert len(first_dashboard["innovations"]) == 9
    assert len(second_dashboard["innovations"]) == 9

    assert len(first_dashboard["claim_candidates"]) == 6
    assert len(second_dashboard["claim_candidates"]) == 6


def test_missing_authentication_is_denied() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Authentication required."
    }

    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_invalid_token_is_denied() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(
            "not-a-valid-token"
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or expired access token."
    }


def test_role_header_cannot_authenticate_request() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard",
        headers={
            "X-User-Role": "admin",
        },
    )

    assert response.status_code == 401


def test_viewer_cannot_access_patent_dashboard() -> None:
    client = build_isolated_client()

    token = create_test_token("viewer")

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(
            token,
            **{
                "X-User-Role": "admin",
            },
        ),
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Permission denied: "
            "view_patent_governance"
        )
    }


def test_unknown_role_fails_closed() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "patent_superuser"
    )

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(token),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid authenticated role."
    }


def test_operator_receives_masked_dashboard() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "operator",
        user_id="operator-001",
    )

    response = client.get(
        (
            "/patent-readiness/dashboard"
            "?include_sensitive=true"
        ),
        headers=bearer_headers(
            token,
            **{
                "X-User-Role": "admin",
            },
        ),
    )

    assert response.status_code == 200

    body = response.text

    assert (
        "CGMS Patent &amp; IP Progress Dashboard"
        in body
        or "CGMS Patent & IP Progress Dashboard"
        in body
    )

    # Confirms the protected production route is enabled.
    assert "Authenticated Access" in body
    assert "Production Access Disabled" not in body

    # Operator must receive the masked view.
    assert "Identifiers Masked" in body
    assert "••••7873" in body
    assert "••••5429" in body
    assert "••••3697" in body

    # Query parameters and role headers must not reveal identifiers.
    assert "63/987,873" not in body
    assert "225429" not in body
    assert "74563697" not in body

    assert (
        'content="noindex, nofollow, noarchive"'
        in body
    )


def test_admin_receives_sensitive_dashboard() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "admin",
        user_id="admin-001",
    )

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(token),
    )

    assert response.status_code == 200

    body = response.text

    # Confirms the protected production route is enabled.
    assert "Authenticated Access" in body
    assert "Production Access Disabled" not in body

    # Admin has the separate sensitive-data permission.
    assert "63/987,873" in body
    assert "8158" in body
    assert "225429" in body
    assert "74563697" in body

    # The masking badge must not appear for an authorized admin.
    assert "Identifiers Masked" not in body


def test_patent_dashboard_disables_caching_and_framing() -> None:
    client = build_isolated_client()

    token = create_test_token("operator")

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(token),
    )

    assert response.status_code == 200

    assert response.headers["cache-control"] == (
        "no-store, no-cache, must-revalidate, "
        "private, max-age=0"
    )

    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"

    assert (
        response.headers["x-content-type-options"]
        == "nosniff"
    )

    assert (
        response.headers["x-frame-options"]
        == "DENY"
    )

    assert (
        response.headers["referrer-policy"]
        == "no-referrer"
    )

    content_security_policy = response.headers[
        "content-security-policy"
    ]

    assert "script-src 'none'" in content_security_policy
    assert "frame-ancestors 'none'" in content_security_policy
    assert "form-action 'none'" in content_security_policy


def test_expired_token_is_denied() -> None:
    client = build_isolated_client()

    token = create_test_token(
        "admin",
        expires_delta=timedelta(
            seconds=-1
        ),
    )

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(token),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or expired access token."
    }


def test_token_signed_with_different_secret_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = create_test_token("admin")

    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        (
            "different-test-secret-key-with-more-"
            "than-32-characters"
        ),
    )

    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard",
        headers=bearer_headers(token),
    )

    assert response.status_code == 401


def test_production_application_registers_protected_dashboard() -> None:
    production_paths = {
        route.path
        for route in production_app.routes
    }

    assert (
        "/patent-readiness/dashboard"
        in production_paths
    )

    with TestClient(production_app) as client:
        response = client.get(
            "/patent-readiness/dashboard"
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Authentication required."
    }