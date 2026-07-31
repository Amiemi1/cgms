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

    milestone_ids = all_milestone_ids(
        dashboard
    )

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
    }.issubset(milestone_ids)

    assert any(
        item["label"] == "Current regression suite"
        and item["value"] == "540 passed"
        for item in dashboard["summary"]
    )

    assert any(
        item["title"] == "SBA-007B closure baseline"
        and item["result"] == "528 passed"
        for item in dashboard["validation"]
    )

    assert any(
        item["label"]
        == "Latest published implementation"
        and item["value"] == "16a673d"
        for item in dashboard["summary"]
    )

    assert any(
        item["title"]
        == "PRG-001 repository publication"
        and item["result"] == "Synchronized"
        and "bcefd77198eceafd086e4e63d150037c061ce0d7"
        in item["detail"]
        for item in dashboard["validation"]
    )

    assert dashboard["commits"][0] == {
        "hash": "16a673d",
        "title": (
            "docs(governance): record CRG-001 "
            "readiness assessment"
        ),
        "status": "Published",
    }

    assert (
        dashboard["page"]["status"]
        == (
            "Complete, regression-validated, committed, "
            "and published; pilot verdict NOT READY"
        )
    )

    assert (
        dashboard["page"]["branch"]
        == "cgms-v2-roadmap"
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

    assert (
        "CGMS Programme Progress Dashboard"
        in body
    )
    assert "536 passed" in body
    assert "PRG-001" in body
    assert "bcefd77" in body
    assert (
        "Complete, production-validated, "
        "committed, and published"
        in body
    )
    assert (
        "/patent-readiness/dashboard"
        in body
    )
    assert (
        "docker compose up -d db"
        in body
    )


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

def test_registry_contains_crg001_readiness_assessment() -> None:
    dashboard = (
        ProgrammeProgressRegistry()
        .build_view()
    )

    assert (
        dashboard["page"]["current_sprint"]
        == "Sprint 20"
    )

    assert (
        dashboard["page"]["current_work"]
        == "CRG-001"
    )

    assert "CRG-001" in all_milestone_ids(
        dashboard
    )

    assert any(
        item["label"] == "Pilot readiness"
        and item["value"] == "NOT READY"
        and "4 P0 blockers" in item["detail"]
        for item in dashboard["summary"]
    )

    sprint_20 = next(
        sprint
        for sprint in dashboard["sprints"]
        if sprint["id"] == "SPRINT-20"
    )

    assert (
        sprint_20["status_class"]
        == "complete"
    )

    assert sprint_20["milestones"] == [
        {
            "id": "CRG-001",
            "title": (
                "CGMS Commercial Readiness "
                "Gap Assessment"
            ),
            "status": (
                "Complete, regression-validated, "
                "committed, and published; "
                "pilot verdict NOT READY"
            ),
            "status_class": "complete",
        },
    ]

    assert any(
        item["title"]
        == "CRG-001 capability assessment"
        and item["result"]
        == "20 capabilities assessed"
        for item in dashboard["validation"]
    )

    assert any(
        item["title"]
        == "CRG-001 pilot readiness verdict"
        and item["result"] == "NOT READY"
        for item in dashboard["validation"]
    )

    assert any(
        item["label"] == "Current regression suite"
        and item["value"] == "540 passed"
        for item in dashboard["summary"]
    )

    assert any(
        item["title"]
        == "CRG-001 complete regression suite"
        and item["result"] == "540 passed"
        and "37 known deprecation warnings"
        in item["detail"]
        for item in dashboard["validation"]
    )

    assert any(
        item["title"]
        == "CRG-001 focused closure suite"
        and item["result"] == "12 passed"
        for item in dashboard["validation"]
    )

    assert any(
        item["title"]
        == "CRG-001 repository publication"
        and item["result"] == "Synchronized"
        and "16a673d80091d72f011ce5755564bdc6f74432ff"
        in item["detail"]
        for item in dashboard["validation"]
    )

    assert any(
        item["label"]
        == "Latest published implementation"
        and item["value"] == "16a673d"
        for item in dashboard["summary"]
    )
