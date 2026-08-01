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
    }.issubset(milestone_ids)

    assert any(
        item["label"] == "Current regression suite"
        and item["value"] == "596 passed"
        for item in dashboard["summary"]
    )

    assert any(
        item["label"] == "Latest published implementation"
        and item["value"] == "05dcb2d"
        for item in dashboard["summary"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187C repository publication"
        and item["result"] == "Synchronized"
        and "595de8fcd5c645a26c4c020028a750a6ee36bffc" in item["detail"]
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187C runtime contracts"
        and item["result"] == "PASS"
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187D governance approval"
        and item["result"] == "Approved — not started"
        and "Planned Work" in item["detail"]
        for item in dashboard["validation"]
    )

    assert [item["hash"] for item in dashboard["commits"][:3]] == [
        "595de8f",
        "4624bf8",
        "05dcb2d",
    ]

    assert dashboard["page"]["status"] == (
        "Step 187C complete, published and reconciled; "
        "Step 187D approved and not started"
    )
    assert dashboard["page"]["branch"] == "cgms-v2-roadmap"


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
    assert "596 passed" in body
    assert "PWI-001-187D" in body
    assert "595de8f" in body
    assert "Step 187C complete, published and reconciled" in body
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

    assert dashboard["page"]["as_of"] == "1 August 2026"
    assert dashboard["page"]["current_sprint"] == "Sprint 22"
    assert dashboard["page"]["current_work"] == "PWI-001 Step 187D"

    sprint_22 = next(
        sprint
        for sprint in dashboard["sprints"]
        if sprint["id"] == "SPRINT-22"
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
            "status": "Approved as Planned Work; not started",
            "status_class": "active",
        },
    ]

    assert any(
        item["title"] == "PWI-001 Step 187C authentication suite"
        and item["result"] == "218 passed"
        and "30 warnings" in item["detail"]
        for item in dashboard["validation"]
    )

    assert any(
        item["title"] == "PWI-001 Step 187C complete regression"
        and item["result"] == "596 passed"
        and "37 warnings" in item["detail"]
        for item in dashboard["validation"]
    )

    assert dashboard["governance"]["classification"] == (
        "Approved Recommended Deviation — "
        "PWI-001 Dashboard Currency Update"
    )
