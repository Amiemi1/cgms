from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.dashboard.main import (
    app as production_app,
)
from app.services.auth import (
    application_authorization
    as authorization_module,
)
from app.services.auth.application_authorization import (
    ApplicationAuthorizationPolicyError,
    CSRF_HEADER_NAME,
    enforce_application_authorization,
    required_permission_for_route,
    required_transport_for_route,
)
from app.services.auth.browser_csrf import (
    BrowserCsrfValidationError,
)


@dataclass(frozen=True)
class StubPrincipal:
    permissions: frozenset[str]
    user_id: str = "1001"
    role: str = "viewer"
    token_id: str = "authorization-test-token"

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        return permission in self.permissions


def build_application() -> FastAPI:
    isolated_app = FastAPI(
        dependencies=[
            Depends(
                enforce_application_authorization
            )
        ]
    )

    @isolated_app.get("/")
    def public_root() -> dict[str, bool]:
        return {
            "public": True,
        }

    @isolated_app.get("/dashboard")
    def protected_dashboard() -> dict[str, bool]:
        return {
            "protected": True,
        }

    @isolated_app.patch(
        "/dashboard/memory/{memory_id}/complete"
    )
    def complete_memory(
        memory_id: int,
    ) -> dict[str, int]:
        return {
            "memory_id": memory_id,
        }

    @isolated_app.post(
        "/admin/browser-sessions/revoke-user"
    )
    def revoke_sessions() -> dict[str, bool]:
        return {
            "revoked": True,
        }

    @isolated_app.get(
        "/product-readiness/capabilities"
    )
    def dual_transport_read() -> dict[str, bool]:
        return {
            "dual": True,
        }

    @isolated_app.get(
        "/patent-readiness/dashboard"
    )
    def browser_only_read() -> dict[str, bool]:
        return {
            "browser": True,
        }

    @isolated_app.get(
        "/audit/records"
    )
    def bearer_only_read() -> dict[str, bool]:
        return {
            "bearer": True,
        }

    return isolated_app


def configure_browser_principal(
    monkeypatch: pytest.MonkeyPatch,
    principal: StubPrincipal,
) -> None:
    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_session_identity",
        lambda request, session_registry: object(),
    )

    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_principal",
        (
            lambda **_kwargs:
            principal
        ),
    )


def test_production_route_permission_mapping_is_complete(
) -> None:
    public_count = 0
    protected_count = 0

    for route in production_app.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        for method in sorted(
            route.methods
        ):
            if method in {
                "HEAD",
                "OPTIONS",
            }:
                continue

            permission = (
                required_permission_for_route(
                    method,
                    route.path,
                )
            )

            if permission is None:
                public_count += 1
            else:
                protected_count += 1

    assert public_count == 4
    assert protected_count == 101


def test_sensitive_read_permission_exceptions(
) -> None:
    assert (
        required_permission_for_route(
            "GET",
            "/audit/records",
        )
        == "view_audit"
    )

    assert (
        required_permission_for_route(
            "GET",
            "/session/history",
        )
        == "view_sessions"
    )

    assert (
        required_permission_for_route(
            "GET",
            "/patent-readiness/dashboard",
        )
        == "view_patent_governance"
    )

    assert (
        required_permission_for_route(
            "GET",
            "/patent-readiness/evidence-package",
        )
        == "view_patent_sensitive"
    )


def test_unknown_unsafe_route_fails_closed(
) -> None:
    with pytest.raises(
        ApplicationAuthorizationPolicyError
    ):
        required_permission_for_route(
            "POST",
            "/future/unmapped-control",
        )


def test_explicit_public_route_is_anonymous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_browser_authentication(
        *args: object,
        **kwargs: object,
    ) -> object:
        raise AssertionError(
            "Public route attempted authentication."
        )

    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_session_identity",
        unexpected_browser_authentication,
    )

    response = TestClient(
        build_application()
    ).get("/")

    assert response.status_code == 200
    assert response.json() == {
        "public": True,
    }


def test_bearer_read_with_permission_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "view_dashboard",
            }
        )
    )

    monkeypatch.setattr(
        authorization_module,
        "get_current_principal",
        lambda **_kwargs: principal,
    )

    response = TestClient(
        build_application()
    ).get(
        "/product-readiness/capabilities",
        headers={
            "Authorization": "Bearer test-token",
        },
    )

    assert response.status_code == 200


def test_explicit_invalid_authorization_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_browser_authentication(
        *args: object,
        **kwargs: object,
    ) -> object:
        raise AssertionError(
            "Invalid Authorization header fell back "
            "to browser authentication."
        )

    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_session_identity",
        unexpected_browser_authentication,
    )

    response = TestClient(
        build_application()
    ).get(
        "/product-readiness/capabilities",
        headers={
            "Authorization": "Basic invalid",
        },
    )

    assert response.status_code == 401


def test_browser_read_with_permission_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "view_dashboard",
            }
        )
    )

    configure_browser_principal(
        monkeypatch,
        principal,
    )

    response = TestClient(
        build_application()
    ).get(
        "/dashboard"
    )

    assert response.status_code == 200


def test_missing_permission_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset()
    )

    configure_browser_principal(
        monkeypatch,
        principal,
    )

    response = TestClient(
        build_application()
    ).get(
        "/dashboard"
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Permission denied: view_dashboard"
    )


def test_browser_mutation_without_csrf_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "manage_memory",
            }
        ),
        role="operator",
    )

    configure_browser_principal(
        monkeypatch,
        principal,
    )

    def reject_csrf(
        request: object,
        *,
        submitted_token: str | None,
    ) -> None:
        raise BrowserCsrfValidationError(
            "Invalid request."
        )

    monkeypatch.setattr(
        authorization_module,
        "validate_browser_csrf_request",
        reject_csrf,
    )

    response = TestClient(
        build_application()
    ).patch(
        "/dashboard/memory/7/complete"
    )

    assert response.status_code == 400


def test_browser_mutation_with_csrf_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "manage_memory",
            }
        ),
        role="operator",
    )

    configure_browser_principal(
        monkeypatch,
        principal,
    )

    submitted_tokens: list[str | None] = []

    def accept_csrf(
        request: object,
        *,
        submitted_token: str | None,
    ) -> None:
        submitted_tokens.append(
            submitted_token
        )

    monkeypatch.setattr(
        authorization_module,
        "validate_browser_csrf_request",
        accept_csrf,
    )

    response = TestClient(
        build_application()
    ).patch(
        "/dashboard/memory/7/complete",
        headers={
            CSRF_HEADER_NAME: "signed-csrf-token",
        },
    )

    assert response.status_code == 200
    assert submitted_tokens == [
        "signed-csrf-token",
    ]


def test_bearer_mutation_does_not_require_csrf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "manage_memory",
            }
        ),
        role="operator",
    )

    monkeypatch.setattr(
        authorization_module,
        "get_current_principal",
        lambda **_kwargs: principal,
    )

    def unexpected_csrf(
        *args: object,
        **kwargs: object,
    ) -> None:
        raise AssertionError(
            "Bearer mutation attempted CSRF validation."
        )

    monkeypatch.setattr(
        authorization_module,
        "validate_browser_csrf_request",
        unexpected_csrf,
    )

    response = TestClient(
        build_application()
    ).patch(
        "/dashboard/memory/7/complete",
        headers={
            "Authorization": "Bearer test-token",
        },
    )

    assert response.status_code == 200


def test_internally_validated_browser_mutation_is_exempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "manage_browser_sessions",
            }
        ),
        role="admin",
    )

    configure_browser_principal(
        monkeypatch,
        principal,
    )

    def unexpected_csrf(
        *args: object,
        **kwargs: object,
    ) -> None:
        raise AssertionError(
            "Internally validated route received "
            "duplicate CSRF validation."
        )

    monkeypatch.setattr(
        authorization_module,
        "validate_browser_csrf_request",
        unexpected_csrf,
    )

    response = TestClient(
        build_application()
    ).post(
        "/admin/browser-sessions/revoke-user"
    )

    assert response.status_code == 200

def test_route_transport_policy_mapping(
) -> None:
    assert (
        required_transport_for_route(
            "GET",
            "/",
        )
        == "public"
    )

    assert (
        required_transport_for_route(
            "GET",
            "/dashboard",
        )
        == "browser"
    )

    assert (
        required_transport_for_route(
            "GET",
            "/audit/records",
        )
        == "bearer"
    )

    assert (
        required_transport_for_route(
            "POST",
            "/adapters/slack",
        )
        == "bearer"
    )

    assert (
        required_transport_for_route(
            "GET",
            "/product-readiness/capabilities",
        )
        == "dual"
    )


def test_browser_only_route_rejects_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_authentication(
        *args: object,
        **kwargs: object,
    ) -> object:
        raise AssertionError(
            "Browser-only route attempted principal "
            "resolution after receiving a Bearer header."
        )

    monkeypatch.setattr(
        authorization_module,
        "get_current_principal",
        unexpected_authentication,
    )

    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_session_identity",
        unexpected_authentication,
    )

    response = TestClient(
        build_application()
    ).get(
        "/patent-readiness/dashboard",
        headers={
            "Authorization": "Bearer test-token",
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Browser session authentication required."
    )


def test_bearer_only_route_rejects_browser_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_browser_authentication(
        *args: object,
        **kwargs: object,
    ) -> object:
        raise AssertionError(
            "Bearer-only route attempted browser "
            "authentication."
        )

    monkeypatch.setattr(
        authorization_module,
        "get_current_browser_session_identity",
        unexpected_browser_authentication,
    )

    response = TestClient(
        build_application()
    ).get(
        "/audit/records"
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Authentication required."
    )


def test_bearer_only_route_accepts_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal = StubPrincipal(
        permissions=frozenset(
            {
                "view_audit",
            }
        ),
        role="viewer",
    )

    monkeypatch.setattr(
        authorization_module,
        "get_current_principal",
        lambda **_kwargs: principal,
    )

    response = TestClient(
        build_application()
    ).get(
        "/audit/records",
        headers={
            "Authorization": "Bearer test-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "bearer": True,
    }

def test_production_application_registers_global_guard(
) -> None:
    registered_dependencies = [
        dependency.dependency
        for dependency
        in production_app.router.dependencies
    ]

    assert (
        enforce_application_authorization
        in registered_dependencies
    )


def test_production_routes_inherit_global_guard(
) -> None:
    protected_route_count = 0

    for route in production_app.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        dependency_calls = [
            dependency.call
            for dependency
            in route.dependant.dependencies
        ]

        assert (
            enforce_application_authorization
            in dependency_calls
        )

        protected_route_count += 1

    assert protected_route_count == 105


def test_production_public_root_remains_anonymous(
) -> None:
    response = TestClient(
        production_app
    ).get("/")

    assert response.status_code == 200
    assert response.json()["system"] == "CGMS"


@pytest.mark.parametrize(
    "path",
    (
        "/dashboard",
        "/operator",
        "/product-readiness/dashboard",
        "/system/health",
        "/audit/records",
    ),
)
def test_production_protected_reads_deny_anonymous(
    path: str,
) -> None:
    response = TestClient(
        production_app
    ).get(path)

    assert response.status_code == 401


def test_production_browser_only_surface_rejects_bearer(
) -> None:
    response = TestClient(
        production_app
    ).get(
        "/dashboard",
        headers={
            "Authorization": "Bearer invalid-test-token",
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Browser session authentication required."
    )
