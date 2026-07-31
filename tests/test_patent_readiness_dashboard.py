from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.main import app as production_app
from app.dashboard.routes.patent_readiness_dashboard import (
    get_patent_dashboard_service,
    router as patent_dashboard_router,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session_dependency import (
    get_current_browser_principal,
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
from app.services.security.rbac_policy import (
    get_permissions,
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


def build_principal(
    role: str,
    *,
    user_id: str = "browser-test-user",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        workspace_id="default",
        user_id=user_id,
        role=role,
        permissions=get_permissions(role),
        token_id=f"{role}-browser-session",
    )


def build_isolated_client(
    *,
    role: str | None = None,
    user_id: str = "browser-test-user",
) -> TestClient:
    isolated_app = FastAPI()

    service = build_service()

    isolated_app.dependency_overrides[
        get_patent_dashboard_service
    ] = lambda: service

    if role is not None:
        principal = build_principal(
            role,
            user_id=user_id,
        )

        isolated_app.dependency_overrides[
            get_current_browser_principal
        ] = lambda: principal

    isolated_app.include_router(
        patent_dashboard_router
    )

    return TestClient(isolated_app)


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


def test_missing_browser_session_is_denied() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Browser session required."
    }

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def test_bearer_token_cannot_authenticate_request() -> None:
    client = build_isolated_client()

    response = client.get(
        "/patent-readiness/dashboard",
        headers={
            "Authorization": "Bearer not-a-browser-session",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Browser session required."
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

    assert response.json() == {
        "detail": "Browser session required."
    }


def test_viewer_cannot_access_patent_dashboard() -> None:
    client = build_isolated_client(
        role="viewer"
    )

    response = client.get(
        "/patent-readiness/dashboard",
        headers={
            "Authorization": "Bearer ignored",
            "X-User-Role": "admin",
        },
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Permission denied: "
            "view_patent_governance"
        )
    }

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


def test_operator_receives_masked_dashboard() -> None:
    client = build_isolated_client(
        role="operator",
        user_id="operator-001",
    )

    response = client.get(
        (
            "/patent-readiness/dashboard"
            "?include_sensitive=true"
        ),
        headers={
            "Authorization": "Bearer ignored",
            "X-User-Role": "admin",
        },
    )

    assert response.status_code == 200

    body = response.text

    assert (
        "CGMS Patent &amp; IP Progress Dashboard"
        in body
        or "CGMS Patent & IP Progress Dashboard"
        in body
    )

    assert "Authenticated Access" in body
    assert "Production Access Disabled" not in body

    assert "Identifiers Masked" in body
    assert "••••7873" in body
    assert "••••5429" in body
    assert "••••3697" in body

    assert "63/987,873" not in body
    assert "225429" not in body
    assert "74563697" not in body

    assert (
        'content="noindex, nofollow, noarchive"'
        in body
    )


def test_admin_receives_sensitive_dashboard() -> None:
    client = build_isolated_client(
        role="admin",
        user_id="admin-001",
    )

    response = client.get(
        "/patent-readiness/dashboard"
    )

    assert response.status_code == 200

    body = response.text

    assert "Authenticated Access" in body
    assert "Production Access Disabled" not in body

    assert "63/987,873" in body
    assert "8158" in body
    assert "225429" in body
    assert "74563697" in body

    assert "Identifiers Masked" not in body


def test_patent_dashboard_disables_caching_and_framing() -> None:
    client = build_isolated_client(
        role="operator"
    )

    response = client.get(
        "/patent-readiness/dashboard"
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
    assert "connect-src 'self'" in content_security_policy
    assert "frame-ancestors 'none'" in content_security_policy
    assert "form-action 'none'" in content_security_policy


def test_production_application_registers_browser_dashboard() -> None:
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
        "detail": "Browser session required."
    }
