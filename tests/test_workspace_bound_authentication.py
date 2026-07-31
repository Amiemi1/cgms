from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest
from fastapi import (
    FastAPI,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
)
from fastapi.testclient import TestClient

from app.dashboard.auth import (
    get_credential_authentication_service,
    router,
)
from app.services.auth.account_authorization import (
    ResolvedAccountAuthorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
    get_current_principal,
)
from app.services.auth.browser_authorization import (
    BrowserSessionAuthorizationError,
    revalidate_browser_session,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
    issue_browser_session_token,
)
from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.jwt_handler import (
    create_access_token,
    decode_access_token,
)
from app.services.security.rbac_policy import (
    get_permissions,
)
from app.services.workspace.repository import (
    WorkspaceRepositoryError,
)
from app.services.workspace.resolution import (
    ResolvedWorkspaceContext,
    get_workspace_context_resolver,
)


class StubWorkspaceFailure(
    WorkspaceRepositoryError
):
    pass


@dataclass
class StubAuthorizationService:
    role: str = "operator"

    def resolve(
        self,
        user_id: str | int,
    ) -> ResolvedAccountAuthorization:
        normalized_user_id = int(
            str(user_id).strip()
        )

        return ResolvedAccountAuthorization(
            user_id=normalized_user_id,
            email="user@example.com",
            stored_role=self.role,
            canonical_role=self.role,
            used_legacy_alias=False,
            permissions=get_permissions(
                self.role
            ),
        )


class StubWorkspaceResolver:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error

        self.calls: list[
            tuple[
                str | int,
                str,
            ]
        ] = []

    def resolve_requested(
        self,
        *,
        user_id: str | int,
        workspace_id: str,
    ) -> ResolvedWorkspaceContext:
        self.calls.append(
            (
                user_id,
                workspace_id,
            )
        )

        if self.error is not None:
            raise self.error

        return ResolvedWorkspaceContext(
            workspace_id=str(
                workspace_id
            ).strip(),
            workspace_name="Resolved Workspace",
            user_id=int(
                str(user_id).strip()
            ),
            membership_id=1,
        )

    def resolve_default(
        self,
        user_id: str | int,
    ) -> ResolvedWorkspaceContext:
        return self.resolve_requested(
            user_id=user_id,
            workspace_id="default",
        )


class StubCredentialService:
    def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> AuthenticatedAccount:
        return AuthenticatedAccount(
            user_id=1001,
            email=email,
            stored_role="operator",
            canonical_role="operator",
            used_legacy_alias=False,
        )


@pytest.fixture(autouse=True)
def configure_jwt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        (
            "pwi-workspace-bound-authentication-"
            "test-secret-with-sufficient-length"
        ),
    )


def bearer_credentials(
    payload: dict[str, str],
) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(
            payload
        ),
    )


def browser_identity(
    *,
    user_id: str = "1001",
    role: str = "operator",
) -> BrowserSessionIdentity:
    issued_at = datetime.now(
        timezone.utc
    )

    return BrowserSessionIdentity(
        user_id=user_id,
        role=role,
        token_id="workspace-browser-session",
        issued_at=issued_at,
        expires_at=(
            issued_at
            + timedelta(minutes=30)
        ),
    )


def test_bearer_principal_is_workspace_bound(
) -> None:
    resolver = StubWorkspaceResolver()

    principal = get_current_principal(
        credentials=bearer_credentials(
            {
                "user_id": "1001",
                "role": "operator",
                "workspace_id":
                    "commercial-intelligence",
            }
        ),
        authorization_service=(
            StubAuthorizationService()
        ),
        workspace_context_resolver=resolver,
    )

    assert isinstance(
        principal,
        AuthenticatedPrincipal,
    )

    assert principal.user_id == "1001"

    assert (
        principal.workspace_id
        == "commercial-intelligence"
    )

    assert principal.role == "operator"

    assert resolver.calls == [
        (
            1001,
            "commercial-intelligence",
        )
    ]


def test_bearer_without_workspace_fails_closed(
) -> None:
    with pytest.raises(
        HTTPException
    ) as error:
        get_current_principal(
            credentials=bearer_credentials(
                {
                    "user_id": "1001",
                    "role": "operator",
                }
            ),
            authorization_service=(
                StubAuthorizationService()
            ),
            workspace_context_resolver=(
                StubWorkspaceResolver()
            ),
        )

    assert error.value.status_code == 401


def test_bearer_role_change_fails_closed(
) -> None:
    with pytest.raises(
        HTTPException
    ) as error:
        get_current_principal(
            credentials=bearer_credentials(
                {
                    "user_id": "1001",
                    "role": "operator",
                    "workspace_id": "default",
                }
            ),
            authorization_service=(
                StubAuthorizationService(
                    role="viewer"
                )
            ),
            workspace_context_resolver=(
                StubWorkspaceResolver()
            ),
        )

    assert error.value.status_code == 401


def test_bearer_inactive_membership_fails_closed(
) -> None:
    resolver = StubWorkspaceResolver(
        error=StubWorkspaceFailure(
            "Membership unavailable."
        )
    )

    with pytest.raises(
        HTTPException
    ) as error:
        get_current_principal(
            credentials=bearer_credentials(
                {
                    "user_id": "1001",
                    "role": "operator",
                    "workspace_id": "default",
                }
            ),
            authorization_service=(
                StubAuthorizationService()
            ),
            workspace_context_resolver=resolver,
        )

    assert error.value.status_code == 401


def test_browser_principal_uses_persistent_workspace(
) -> None:
    resolver = StubWorkspaceResolver()

    principal = revalidate_browser_session(
        identity=browser_identity(),
        workspace_id="commercial-intelligence",
        service=StubAuthorizationService(),
        workspace_context_resolver=resolver,
    )

    assert (
        principal.workspace_id
        == "commercial-intelligence"
    )

    assert resolver.calls == [
        (
            1001,
            "commercial-intelligence",
        )
    ]


def test_browser_workspace_denial_is_non_disclosing(
) -> None:
    resolver = StubWorkspaceResolver(
        error=StubWorkspaceFailure(
            "Membership unavailable."
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=browser_identity(),
            workspace_id="other-workspace",
            service=StubAuthorizationService(),
            workspace_context_resolver=resolver,
        )

    assert str(error.value) == (
        "Browser session is no longer authorized."
    )


def test_legacy_login_issues_workspace_bound_bearer(
) -> None:
    app = FastAPI()

    app.include_router(
        router
    )

    app.dependency_overrides[
        get_credential_authentication_service
    ] = lambda: StubCredentialService()

    app.dependency_overrides[
        get_workspace_context_resolver
    ] = lambda: StubWorkspaceResolver()

    response = TestClient(
        app
    ).post(
        "/login",
        json={
            "email": "user@example.com",
            "password": "valid-password",
        },
    )

    assert response.status_code == 200

    payload = decode_access_token(
        response.json()[
            "access_token"
        ]
    )

    assert payload is not None
    assert payload["user_id"] == "1001"
    assert payload["role"] == "operator"
    assert payload["workspace_id"] == "default"


def test_browser_jwt_remains_workspace_neutral(
) -> None:
    account = AuthenticatedAccount(
        user_id=1001,
        email="user@example.com",
        stored_role="operator",
        canonical_role="operator",
        used_legacy_alias=False,
    )

    payload = decode_access_token(
        issue_browser_session_token(
            account
        )
    )

    assert payload is not None

    assert (
        "workspace_id"
        not in payload
    )
