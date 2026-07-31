from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.routes.browser_auth import (
    router,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session_dependency import (
    get_current_browser_principal,
)
from app.services.security.rbac_policy import (
    get_permissions,
)


TEST_JWT_SECRET = (
    "cgms-authenticated-csrf-test-secret-"
    "with-more-than-32-characters"
)

CSRF_COOKIE_NAME = "__Host-cgms_csrf"


@pytest.fixture(autouse=True)
def configure_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        TEST_JWT_SECRET,
    )

    monkeypatch.setenv(
        "CGMS_JWT_ISSUER",
        "cgms-authenticated-csrf-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-authenticated-csrf-dashboard",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_COOKIE_NAME",
        CSRF_COOKIE_NAME,
    )

    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        "600",
    )


def build_principal(
    *,
    role: str = "operator",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        workspace_id="default",
        user_id="1001",
        role=role,
        permissions=get_permissions(
            role
        ),
        token_id=(
            "authenticated-browser-session"
        ),
    )


def build_app(
    *,
    authenticated: bool = True,
    role: str = "operator",
) -> FastAPI:
    app = FastAPI()

    app.include_router(
        router
    )

    if authenticated:
        principal = build_principal(
            role=role
        )

        app.dependency_overrides[
            get_current_browser_principal
        ] = lambda: principal

    return app


def build_client(
    *,
    authenticated: bool = True,
    role: str = "operator",
) -> TestClient:
    return TestClient(
        build_app(
            authenticated=authenticated,
            role=role,
        ),
        base_url="https://testserver",
    )


@pytest.mark.parametrize(
    "role",
    [
        "admin",
        "operator",
        "viewer",
    ],
)
def test_authenticated_role_can_obtain_csrf_token(
    role: str,
) -> None:
    client = build_client(
        role=role
    )

    response = client.get(
        "/auth/csrf"
    )

    assert response.status_code == 200

    payload = response.json()

    assert isinstance(
        payload.get("csrf_token"),
        str,
    )

    assert payload["csrf_token"]

    csrf_cookie = response.cookies.get(
        CSRF_COOKIE_NAME
    )

    assert csrf_cookie is not None

    assert (
        csrf_cookie
        == payload["csrf_token"]
    )


def test_csrf_cookie_uses_hardened_attributes(
) -> None:
    response = build_client().get(
        "/auth/csrf"
    )

    set_cookie_header = (
        response.headers.get(
            "set-cookie",
            "",
        )
    )

    assert CSRF_COOKIE_NAME in (
        set_cookie_header
    )

    assert "Secure" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "SameSite=strict" in (
        set_cookie_header
    )

    assert "Path=/" in (
        set_cookie_header
    )


def test_authenticated_csrf_response_is_not_cached(
) -> None:
    response = build_client().get(
        "/auth/csrf"
    )

    assert response.status_code == 200

    assert (
        response.headers["cache-control"]
        == "no-store, max-age=0"
    )

    assert (
        response.headers["pragma"]
        == "no-cache"
    )

    assert response.headers["expires"] == "0"


def test_missing_browser_session_is_denied(
) -> None:
    response = build_client(
        authenticated=False
    ).get(
        "/auth/csrf"
    )

    assert response.status_code == 401


def test_csrf_endpoint_is_get_only(
) -> None:
    response = build_client().post(
        "/auth/csrf"
    )

    assert response.status_code == 405
