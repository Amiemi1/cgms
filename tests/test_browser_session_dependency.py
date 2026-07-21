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
    SESSION_TOKEN_USE,
    issue_browser_session_token,
)
from app.services.auth.browser_session_dependency import (
    get_account_authorization_service,
    get_current_browser_principal,
    require_browser_permission,
)
from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.jwt_handler import (
    create_access_token,
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
) -> FastAPI:
    app = FastAPI()

    active_service = (
        authorization_service
        or StubAccountAuthorizationService()
    )

    app.dependency_overrides[
        get_account_authorization_service
    ] = lambda: active_service

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
    client = TestClient(
        build_app()
    )

    response = client.get(
        "/session"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Browser session required."
    }

    assert (
        response.headers["cache-control"]
        == "no-store"
    )


def test_invalid_browser_session_is_denied() -> None:
    client = TestClient(
        build_app()
    )

    response = client.get(
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


def test_ordinary_access_token_is_not_browser_session() -> None:
    token = create_access_token(
        {
            "user_id": "1001",
            "role": "admin",
        }
    )

    response = TestClient(
        build_app()
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401


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

    response = TestClient(
        build_app()
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

    response = TestClient(
        build_app()
    ).get(
        "/session",
        headers=cookie_headers(
            token
        ),
    )

    assert response.status_code == 401


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
            service
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
            service
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
            service
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