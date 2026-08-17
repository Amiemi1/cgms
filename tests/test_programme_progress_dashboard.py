from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.routes.programme_progress_dashboard import (
    router,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session_dependency import (
    get_current_browser_principal,
)
from app.services.programme_progress.registry import (
    ProgrammeProgressRegistry,
)
from app.services.security.rbac_policy import (
    VIEW_DASHBOARD,
)


def build_client(
    permissions: frozenset[str],
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    principal = AuthenticatedPrincipal(
        workspace_id="default",
        user_id="progress-test-user",
        role="viewer",
        permissions=permissions,
        token_id="progress-test-token",
    )

    app.dependency_overrides[
        get_current_browser_principal
    ] = lambda: principal

    return TestClient(app)


def all_milestone_ids(
    dashboard: dict[str, object],
) -> set[str]:
    return {
        milestone["id"]
        for sprint in dashboard["sprints"]
        for milestone in sprint["milestones"]
    }


def test_registry_contains_governed_progress() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    milestone_ids = all_milestone_ids(dashboard)

    assert {
        "PRE-001",
        "PRE-007",
        "PIP-001",
        "PIP-007",
        "SBA-001D",
        "SBA-003",
        "SBA-004",
        "SBA-005",
        "SBA-006",
        "SBA-007A",
        "SBA-007B",
        "PRG-001",
        "CRG-001",
        "PWI-001-187C",
        "PWI-001-187D",
        "PWI-001-187E",
        "PWI-001-187F",
    }.issubset(milestone_ids)

    assert any(
        item["label"] == "Current regression suite"
        and item["value"] == "679 passed"
        for item in dashboard["summary"]
    )

    assert any(
        item["label"] == "Step 187F technical validation"
        and item["value"] == "679 + live PASS"
        for item in dashboard["summary"]
    )

    assert any(
        item["label"] == "Latest published checkpoint"
        and item["value"] == "6b8a00d"
        for item in dashboard["summary"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187E controlled publication"
        and item["result"] == "Complete — published"
        and "0140d4a26d2e814879c7e5c4a74451cf18f85d92"
        in item["detail"]
        and "18 focused contracts" in item["detail"]
        and "52 selected" in item["detail"]
        and "116-route" in item["detail"]
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187C runtime contracts"
        and item["result"] == "PASS"
        for item in dashboard["validation"]
    )

    assert [item["hash"] for item in dashboard["commits"][:4]] == [
        "6b8a00d",
        "4a43f40",
        "0140d4a",
        "cc366ed",
    ]

    assert dashboard["page"]["status"] == (
        "Step 187F technical closure complete and validated; "
        "governance currency recorded; publication pending "
        "separate explicit approval"
    )
    assert dashboard["page"]["branch"] == "cgms-v2-roadmap"
    assert dashboard["governance"]["classification"] == (
        "Approved Governance Currency Closure — "
        "PWI-001 Step 187F Integrated Isolation"
    )


def test_registry_contains_all_html_interfaces() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    paths = {
        item["path"]
        for item in dashboard["navigation"]
    }

    assert {
        "/progress",
        "/dashboard",
        "/operator",
        "/product-readiness/dashboard",
        "/patent-readiness/dashboard",
        "/auth/login",
    }.issubset(paths)


def test_registry_contains_startup_commands() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    commands = "\n".join(
        item["command"]
        for item in dashboard["startup"]
    )

    assert "docker compose up -d db" in commands
    assert (
        "app.dashboard.main:app"
        in commands
    )
    assert "--ssl-certfile" in commands
    assert (
        "production_preflight.py"
        in commands
    )


def test_registry_returns_isolated_copies() -> None:
    registry = ProgrammeProgressRegistry()

    first = registry.build_view()
    first["page"]["title"] = "Changed"

    second = registry.build_view()

    assert (
        second["page"]["title"]
        == "CGMS Programme Progress Dashboard"
    )


def test_authorized_viewer_can_open_progress() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 200

    body = response.text

    assert "CGMS Programme Progress Dashboard" in body
    assert "679 passed" in body
    assert "PWI-001-187D" in body
    assert "PWI-001-187E" in body
    assert "6b8a00d" in body
    assert "0140d4a" in body
    assert "Run #34" in body
    assert "Step 187F technical closure complete and validated" in body
    assert "publication pending separate explicit approval" in body
    assert "/patent-readiness/dashboard" in body
    assert "docker compose up -d db" in body


def test_progress_denies_missing_permission() -> None:
    with build_client(
        frozenset()
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            "Permission denied: "
            "view_dashboard"
        )
    }


def test_progress_applies_security_headers() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert (
        response.headers["cache-control"]
        == (
            "no-store, no-cache, "
            "must-revalidate, private, max-age=0"
        )
    )
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
    assert (
        "script-src 'none'"
        in response.headers[
            "content-security-policy"
        ]
    )


def test_authenticated_dashboard_templates_include_progress_navigation(
) -> None:
    templates = (
        "dashboard.html",
        "operator_console.html",
        "product_readiness_dashboard.html",
        "patent_readiness_dashboard.html",
    )

    required_paths = {
        "/progress",
        "/dashboard",
        "/operator",
        "/product-readiness/dashboard",
        "/patent-readiness/dashboard",
    }

    template_root = (
        Path("app/dashboard/templates")
    )

    for template_name in templates:
        text = (
            template_root
            .joinpath(template_name)
            .read_text(
                encoding="utf-8",
            )
        )

        assert (
            'aria-label="CGMS dashboard navigation"'
            in text
        )

        for route_path in required_paths:
            assert route_path in text

def test_registry_preserves_crg001_readiness_assessment() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    assert "CRG-001" in all_milestone_ids(dashboard)

    assert any(
        item["label"] == "Pilot readiness"
        and item["value"] == "NOT READY"
        for item in dashboard["summary"]
    )

    sprint_20 = next(
        sprint
        for sprint in dashboard["sprints"]
        if sprint["id"] == "SPRINT-20"
    )

    assert sprint_20["status_class"] == "complete"
    assert sprint_20["milestones"][0]["id"] == "CRG-001"

    assert any(
        item["title"] == "CRG-001 capability assessment"
        and item["result"] == "20 capabilities assessed"
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "CRG-001 complete regression suite"
        and item["result"] == "540 passed"
        and "37 known deprecation warnings" in item["detail"]
        for item in dashboard["validation"]
    )


def test_registry_contains_pwi001_current_state() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    assert dashboard["page"]["as_of"] == "13 August 2026"
    assert dashboard["page"]["current_sprint"] == "Sprint 22"
    assert dashboard["page"]["current_work"] == (
        "PWI-001 Step 187F / Governance-Currency Closure"
    )
    assert dashboard["current_focus"][0] == (
        "PWI-001 Step 187F integrated isolation technical closure complete"
    )
    assert dashboard["upcoming"] == [
        "Separate approval required before controlled staging",
        "Separate approval required before commit or push",
        "Post-publication CI verification only after publication",
    ]
    assert "unrelated repository mutation" in dashboard["governance"]["boundaries"]

    sprint_22 = next(
        sprint
        for sprint in dashboard["sprints"]
        if sprint["id"] == "SPRINT-22"
    )

    assert sprint_22["status"] == (
        "Steps 187D and 187E published; Step 187F technical "
        "closure complete and governance currency recorded"
    )
    assert sprint_22["status_class"] == "active"

    assert sprint_22["milestones"] == [
        {
            "id": "PWI-001-187C",
            "title": "Workspace-Bound Authentication Principals",
            "status": (
                "Complete, validated, published "
                "and reconciled"
            ),
            "status_class": "complete",
        },
        {
            "id": "PWI-001-187D",
            "title": (
                "Tenant Persistence and "
                "Query-Contract Integration"
            ),
            "status": (
                "Complete, database-validated, canonically "
                "closed, committed and published"
            ),
            "status_class": "complete",
        },
        {
            "id": "PWI-001-187E",
            "title": "Active Browser Workspace Switching",
            "status": (
                "Complete, validated, canonically closed, "
                "committed and published"
            ),
            "status_class": "complete",
        },
        {
            "id": "PWI-001-187F",
            "title": (
                "Cross-Workspace Isolation and "
                "Integrated Closure"
            ),
            "status": (
                "Technical closure complete and validated; "
                "governance currency recorded; publication pending"
            ),
            "status_class": "active",
        },
    ]

    assert any(
        item["title"] == "PWI-001 Step 187E controlled publication"
        and item["result"] == "Complete — published"
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "Product Readiness CI recovery closure"
        and item["result"] == "PASS — GitHub Actions"
        and "6b8a00dcc9ad597038a423591dd8aaf731593fa5"
        in item["detail"]
        and "run #34" in item["detail"]
        and "651 passed" in item["detail"]
        for item in dashboard["validation"]
    )


def test_registry_contains_approved_executive_value_model() -> None:
    dashboard = ProgrammeProgressRegistry().build_view()
    value = dashboard["executive_value"]

    assert value["completion"]["overall_percent"] == 44
    assert value["completion"]["product_readiness_percent"] == 23
    assert value["completion"]["pilot_readiness_percent"] == 29

    assert value["headline"]["as_is_base_usd_m"] == 1.5
    assert value["headline"]["as_is_base_ngn_bn"] == 2.04
    assert value["headline"]["next_gate"] == "Pilot Ready"

    assert len(value["value_gates"]) == 5
    assert len(value["value_story"]) == 8

    assert value["model"]["classification"] == (
        "Governed management planning estimate — "
        "not a formal investment valuation"
    )


def test_progress_renders_executive_value_and_value_story() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 200

    body = response.text

    assert "Executive Product &amp; Value" in body
    assert "Overall CGMS Completion" in body
    assert "44%" in body
    assert "As-Is Base Value" in body
    assert "$1.5m" in body
    assert "CGMS Value Story" in body
    assert "Industry Need" in body
    assert "Customer Benefit" in body
    assert "Economic Value" in body
    assert "Persistent organizational memory" in body
    assert "Market Position" in body
    assert "Competitor Comparison" in body
    assert "Glean" in body
    assert "Microsoft 365 Copilot" in body
    assert "Notion AI" in body
    assert "Slack AI / Enterprise" in body
    assert "Cross-system search and connectors" in body
    assert "not a formal investment valuation" in body


def test_progress_renders_visual_value_unlock_story() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 200

    body = response.text

    assert "53.3×" in body
    assert "As-Is → Scale" in body
    assert "Value unlocked +$1.5m" in body
    assert "Value unlocked +$5.0m" in body
    assert "Value unlocked +$17.0m" in body
    assert "Value unlocked +$55.0m" in body
    assert 'class="executive-summary-grid"' in body
    assert 'class="value-gate-grid"' in body
    assert "commercial-highlight" in body
    assert "confidence-pill" in body


def test_progress_renders_buyer_intelligence_opportunity_layer() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 200

    body = response.text

    assert "Client &amp; Strategic Buyer Opportunity" in body
    assert "Buyer Universe Unlocked" in body
    assert "Enterprise Client Opportunity" in body
    assert "Strategic Platform Opportunity" in body
    assert "Strategic Fit Score" in body

    assert "MTN Group" in body
    assert "Standard Bank Group" in body
    assert "Access Bank" in body
    assert "NNPC Ltd" in body
    assert "Airtel Africa" in body
    assert "Dangote Cement" in body
    assert "ServiceNow" in body
    assert "Microsoft" in body

    assert "95/100" in body
    assert "94/100" in body
    assert "91/100" in body
    assert "90/100" in body
    assert "86/100" in body
    assert "83/100" in body
    assert "87/100" in body

    assert "What They Have Today" in body
    assert "Strategic Gap Hypothesis" in body
    assert "Why CGMS Fits" in body
    assert "Initial Use Case" in body
    assert "Governance note:" in body

    assert (
        "does not imply customer status"
        in body
    )

    assert 'id="buyer-opportunity"' in body
    assert 'href="#buyer-opportunity"' in body


def test_progress_renders_auditable_buyer_scores_and_evidence_basis() -> None:
    with build_client(
        frozenset({VIEW_DASHBOARD})
    ) as client:
        response = client.get("/progress")

    assert response.status_code == 200

    body = response.text

    assert "Evidence basis:" in body
    assert "buyer-score-components" in body
    assert "buyer-score-component" in body

    assert "Need" in body
    assert "Stack" in body
    assert "AI" in body
    assert "Scale" in body
    assert "Access" in body

    assert (
        "Official MTN investor, Genova AI and Azure partnership"
        in body
    )

    assert (
        "Official ServiceNow Enterprise Graph and partner-programme"
        in body
    )

    assert (
        "Official Microsoft Copilot connector, Graph, agent and"
        in body
    )
