from __future__ import annotations

from typing import Annotated

import pytest
from fastapi import (
    Depends,
    FastAPI,
)
from fastapi.testclient import TestClient

from app.services.auth.account_authorization import (
    AccountNotFoundError,
    AccountRoleConfigurationError,
    ResolvedAccountAuthorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
    SESSION_TOKEN_USE,
    issue_browser_session_token,
)
from app.services.auth.browser_session_dependency import (
    get_account_authorization_service,
    get_browser_session_registry,
    get_current_browser_principal,
    require_browser_permission,
)
from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.jwt_handler import (
    create_access_token,
)
from app.services.auth.session_registry import (
    BrowserSessionNotRegisteredError,
    BrowserSessionRecordMismatchError,
    BrowserSessionRevokedError,
)
from app.services.security.rbac_policy import (
    VIEW_PATENT_GOVERNANCE,
    get_permissions,
)


TEST_JWT_SECRET = (
    "cgms-browser-dependency-test-secret-"
    "with-more-than-32-characters"
)


@pytest.fixture(autouse=True)
def configure_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        "cgms-browser-dependency-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-browser-dependency-dashboard",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        "__Host-cgms_session",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        "30",
    )


ROLE_USER_IDS = {
    "admin": 1001,
    "operator": 2001,
    "viewer": 3001,
}


DEFAULT_ROLE_BY_USER_ID = {
    user_id: role
    for role, user_id in ROLE_USER_IDS.items()
}


class StubAccountAuthorizationService:
    def __init__(
        self,
        *,
        role_overrides: dict[int, str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.role_overrides = (
            role_overrides or {}
        )

        self.error = error

        self.calls: list[
            str | int
        ] = []

    def resolve(
        self,
        user_id: str | int,
    ) -> ResolvedAccountAuthorization:
        self.calls.append(
            user_id
        )

        if self.error is not None:
            raise self.error

        normalized_user_id = int(
            str(user_id).strip()
        )

        role = self.role_overrides.get(
            normalized_user_id,
            DEFAULT_ROLE_BY_USER_ID.get(
                normalized_user_id
            ),
        )

        if role is None:
            raise AccountNotFoundError(
                "Authenticated account is unavailable."
            )

        return ResolvedAccountAuthorization(
            user_id=normalized_user_id,
            email=(
                f"user-{normalized_user_id}"
                "@example.com"
            ),
            stored_role=role,
            canonical_role=role,
            used_legacy_alias=False,
            permissions=get_permissions(
                role
            ),
        )


class StubBrowserSessionRegistry:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.calls: list[
            BrowserSessionIdentity
        ] = []

    def require_active(
        self,
        identity: BrowserSessionIdentity,
    ) -> object:
        self.calls.append(
            identity
        )

        if self.error is not None:
            raise self.error

        return object()


def build_account(
    role: str,
    *,
    user_id: int | None = None,
) -> AuthenticatedAccount:
    resolved_user_id = (
        user_id
        if user_id is not None
        else ROLE_USER_IDS[role]
    )

    return AuthenticatedAccount(
        user_id=resolved_user_id,
        email="user@example.com",
        stored_role=role,
        canonical_role=role,
        used_legacy_alias=False,
    )


def build_app(
    authorization_service: (
        StubAccountAuthorizationService
        | None
    ) = None,
    session_registry: (
        StubBrowserSessionRegistry
        | None
    ) = None,
) -> FastAPI:
    app = FastAPI()

    active_authorization_service = (
        authorization_service
        or StubAccountAuthorizationService()
    )

    active_session_registry = (
        session_registry
        or StubBrowserSessionRegistry()
    )

    app.dependency_overrides[
        get_account_authorization_service
    ] = lambda: active_authorization_service

    app.dependency_overrides[
        get_browser_session_registry
    ] = lambda: active_session_registry

    @app.get("/session")
    def session_endpoint(
        principal: Annotated[
            AuthenticatedPrincipal,
            Depends(
                get_current_browser_principal
            ),
        ],
    ) -> dict[str, object]:
        return {
            "user_id": principal.user_id,
            "role": principal.role,
            "permissions": sorted(
                principal.permissions
            ),
            "token_id": principal.token_id,
        }

    @app.get("/patent")
    def patent_endpoint(
        principal: Annotated[
            AuthenticatedPrincipal,
            Depends(
                require_browser_permission(
                    VIEW_PATENT_GOVERNANCE
                )
            ),
        ],
    ) -> dict[str, str]:
        return {
            "user_id": principal.user_id,
            "role": principal.role,
        }

    return app


def cookie_headers(
    token: str,
    *,
    cookie_name: str = "__Host-cgms_session",
    **additional_headers: str,
) -> dict[str, str]:
    headers = {
        "Cookie": (
            f"{cookie_name}={token}"
        ),
    }

    headers.update(
        additional_headers
    )

    return headers


def test_missing_browser_session_is_denied() -> None:
    registry = StubBrowserSessionRegistry()

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Browser session required."
    }

    assert registry.calls == []

    assert (
        response.headers["cache-control"]
        == "no-store"
    )


def test_invalid_browser_session_is_denied() -> None:
    registry = StubBrowserSessionRegistry()

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            "not-a-valid-session"
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Invalid or expired browser session."
        )
    }

    assert registry.calls == []


def test_ordinary_access_token_is_not_browser_session() -> None:
    token = create_access_token(
        {
            "user_id": "1001",
            "role": "admin",
        }
    )

    registry = StubBrowserSessionRegistry()

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401
    assert registry.calls == []


def test_authorization_header_is_not_browser_session() -> None:
    token = issue_browser_session_token(
        build_account(
            "admin"
        )
    )

    response = TestClient(
        build_app()
    ).get(
        "/session",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 401


def test_valid_operator_session_creates_principal() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator",
            user_id=2001,
        )
    )

    registry = StubBrowserSessionRegistry()

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["user_id"] == "2001"
    assert payload["role"] == "operator"

    assert (
        VIEW_PATENT_GOVERNANCE
        in payload["permissions"]
    )

    assert payload["token_id"]

    assert len(registry.calls) == 1

    assert (
        registry.calls[0].token_id
        == payload["token_id"]
    )


def test_unregistered_session_is_denied() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    registry = StubBrowserSessionRegistry(
        error=BrowserSessionNotRegisteredError(
            "Browser session is not registered."
        )
    )

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer active."
        )
    }

    assert (
        response.headers["cache-control"]
        == "no-store"
    )


def test_revoked_session_is_denied() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    registry = StubBrowserSessionRegistry(
        error=BrowserSessionRevokedError(
            "Browser session is revoked."
        )
    )

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer active."
        )
    }


def test_mismatched_session_record_is_denied() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    registry = StubBrowserSessionRegistry(
        error=BrowserSessionRecordMismatchError(
            "Browser session record does not match."
        )
    )

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer active."
        )
    }


def test_operator_has_patent_permission() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    response = TestClient(
        build_app()
    ).get(
        "/patent",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 200

    assert (
        response.json()["role"]
        == "operator"
    )


def test_viewer_is_denied_patent_permission() -> None:
    token = issue_browser_session_token(
        build_account(
            "viewer"
        )
    )

    response = TestClient(
        build_app()
    ).get(
        "/patent",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 403

    assert response.json() == {
        "detail": (
            "Permission denied: "
            "view_patent_governance"
        )
    }


def test_role_header_cannot_elevate_viewer() -> None:
    token = issue_browser_session_token(
        build_account(
            "viewer"
        )
    )

    response = TestClient(
        build_app()
    ).get(
        "/patent",
        headers=cookie_headers(
            token,
            **{
                "X-User-Role": "admin",
            },
        ),
    )

    assert response.status_code == 403


def test_unknown_role_session_fails_closed() -> None:
    token = create_access_token(
        {
            "user_id": "1001",
            "role": "superuser",
            "token_use": SESSION_TOKEN_USE,
        }
    )

    registry = StubBrowserSessionRegistry()

    response = TestClient(
        build_app(
            session_registry=registry
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401
    assert registry.calls == []


def test_custom_configured_cookie_name_is_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        "__Host-cgms_patent_session",
    )

    token = issue_browser_session_token(
        build_account(
            "admin"
        )
    )

    client = TestClient(
        build_app()
    )

    wrong_cookie_response = client.get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert (
        wrong_cookie_response.status_code
        == 401
    )

    correct_cookie_response = client.get(
        "/session",
        headers=cookie_headers(
            token,
            cookie_name=(
                "__Host-cgms_patent_session"
            ),
        ),
    )

    assert (
        correct_cookie_response.status_code
        == 200
    )


def test_empty_permission_definition_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="non-empty browser permission",
    ):
        require_browser_permission(
            " "
        )


def test_database_role_change_invalidates_session() -> None:
    token = issue_browser_session_token(
        build_account(
            "admin"
        )
    )

    service = StubAccountAuthorizationService(
        role_overrides={
            ROLE_USER_IDS["admin"]: "operator",
        }
    )

    response = TestClient(
        build_app(
            authorization_service=service
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer authorized."
        )
    }

    assert (
        response.headers["cache-control"]
        == "no-store"
    )


def test_deleted_database_account_invalidates_session() -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    service = StubAccountAuthorizationService(
        error=AccountNotFoundError(
            "Authenticated account is unavailable."
        )
    )

    response = TestClient(
        build_app(
            authorization_service=service
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer authorized."
        )
    }


def test_invalid_database_role_configuration_invalidates_session(
) -> None:
    token = issue_browser_session_token(
        build_account(
            "operator"
        )
    )

    service = StubAccountAuthorizationService(
        error=AccountRoleConfigurationError(
            "Account role configuration is invalid."
        )
    )

    response = TestClient(
        build_app(
            authorization_service=service
        )
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": (
            "Browser session is no longer authorized."
        )
    }