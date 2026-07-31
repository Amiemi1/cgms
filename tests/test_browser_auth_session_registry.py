from __future__ import annotations

from html.parser import HTMLParser

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.routes.browser_auth import (
    get_browser_login_security_service,
    get_credential_authentication_service,
    router,
)
from app.services.auth.browser_csrf import (
    issue_browser_csrf_token,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
    decode_browser_session_token,
    issue_browser_session_token,
)
from app.services.auth.browser_session_dependency import (
    get_browser_session_registry,
)
from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.login_throttle import (
    LoginThrottleDecision,
)
from app.services.auth.session_registry import (
    BrowserSessionNotRegisteredError,
    BrowserSessionRecordConflictError,
    BrowserSessionRegistryError,
    BrowserSessionRevokedError,
)
from app.services.workspace.resolution import (
    ResolvedWorkspaceContext,
    get_workspace_context_resolver,
)


TEST_JWT_SECRET = (
    "cgms-browser-auth-registry-test-secret-"
    "with-more-than-32-characters"
)

SESSION_COOKIE_NAME = "__Host-cgms_session"
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
        "cgms-browser-auth-registry-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-browser-auth-registry-dashboard",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        SESSION_COOKIE_NAME,
    )

    monkeypatch.setenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        "30",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_COOKIE_NAME",
        CSRF_COOKIE_NAME,
    )

    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        "600",
    )


class CsrfInputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.token: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[
            tuple[str, str | None]
        ],
    ) -> None:
        if tag != "input":
            return

        attributes = dict(attrs)

        if (
            attributes.get("name")
            == "csrf_token"
        ):
            self.token = attributes.get(
                "value"
            )




class StubLoginSecurityService:
    """
    Isolated login-security test double.

    Throttling behaviour is tested directly in
    test_login_throttle.py and test_browser_auth.py.
    These session-registry tests exercise only the ordering and
    failure behaviour of browser-session registration.
    """

    def resolve_network_identifier(
        self,
        request,
    ) -> str:
        return "203.0.113.90"

    def check(
        self,
        *,
        email: str,
        network_identifier: str,
    ) -> LoginThrottleDecision:
        return LoginThrottleDecision.allowed()

    def record_failure(
        self,
        *,
        email: str,
        network_identifier: str,
    ) -> LoginThrottleDecision:
        return LoginThrottleDecision.allowed()

    def record_success(
        self,
        *,
        email: str,
        network_identifier: str,
        user_id: int,
    ) -> None:
        return None

    def record_invalid_request(
        self,
        *,
        network_identifier: str,
    ) -> LoginThrottleDecision:
        return LoginThrottleDecision.allowed()


class StubCredentialService:
    def __init__(
        self,
        account: AuthenticatedAccount,
    ) -> None:
        self.account = account

        self.calls: list[
            tuple[str, str]
        ] = []

    def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> AuthenticatedAccount:
        self.calls.append(
            (
                email,
                password,
            )
        )

        return self.account


class StubWorkspaceContextResolver:
    def __init__(
        self,
        workspace_id: str = "default",
    ) -> None:
        self.workspace_id = workspace_id

        self.calls: list[
            str | int
        ] = []

    def resolve_default(
        self,
        user_id: str | int,
    ) -> ResolvedWorkspaceContext:
        self.calls.append(
            user_id
        )

        return ResolvedWorkspaceContext(
            workspace_id=self.workspace_id,
            workspace_name=(
                "Default Workspace"
            ),
            user_id=int(user_id),
            membership_id=1,
        )

class StubSessionRegistry:
    def __init__(
        self,
        *,
        register_error: (
            BrowserSessionRegistryError
            | None
        ) = None,
        require_active_error: (
            BrowserSessionRegistryError
            | None
        ) = None,
        revoke_error: (
            BrowserSessionRegistryError
            | None
        ) = None,
    ) -> None:
        self.register_error = register_error

        self.require_active_error = (
            require_active_error
        )

        self.revoke_error = revoke_error

        self.register_calls: list[
            tuple[
                BrowserSessionIdentity,
                str,
            ]
        ] = []

        self.require_active_calls: list[
            BrowserSessionIdentity
        ] = []

        self.revoke_calls: list[
            tuple[
                BrowserSessionIdentity,
                str,
                str | int | None,
            ]
        ] = []

    def register(
        self,
        identity: BrowserSessionIdentity,
        *,
        workspace_id: str,
    ) -> object:
        self.register_calls.append(
            (
                identity,
                workspace_id,
            )
        )

        if self.register_error is not None:
            raise self.register_error

        return object()

    def require_active(
        self,
        identity: BrowserSessionIdentity,
    ) -> object:
        self.require_active_calls.append(
            identity
        )

        if (
            self.require_active_error
            is not None
        ):
            raise self.require_active_error

        return object()

    def revoke(
        self,
        identity: BrowserSessionIdentity,
        *,
        reason: str = "logout",
        revoked_by_user_id: (
            str | int | None
        ) = None,
    ) -> object:
        self.revoke_calls.append(
            (
                identity,
                reason,
                revoked_by_user_id,
            )
        )

        if self.revoke_error is not None:
            raise self.revoke_error

        return object()


def build_account() -> AuthenticatedAccount:
    return AuthenticatedAccount(
        user_id=1001,
        email="operator@example.com",
        stored_role="operator",
        canonical_role="operator",
        used_legacy_alias=False,
    )


def build_app(
    registry: StubSessionRegistry,
) -> FastAPI:
    app = FastAPI()

    credential_service = (
        StubCredentialService(
            build_account()
        )
    )

    login_security_service = (
        StubLoginSecurityService()
    )

    app.include_router(
        router
    )

    app.dependency_overrides[
        get_credential_authentication_service
    ] = lambda: credential_service

    app.dependency_overrides[
        get_browser_login_security_service
    ] = lambda: login_security_service

    app.dependency_overrides[
        get_browser_session_registry
    ] = lambda: registry

    workspace_context_resolver = (
        StubWorkspaceContextResolver()
    )

    app.dependency_overrides[
        get_workspace_context_resolver
    ] = lambda: (
        workspace_context_resolver
    )

    return app


def build_client(
    registry: StubSessionRegistry,
) -> TestClient:
    return TestClient(
        build_app(registry),
        base_url="https://testserver",
    )


def extract_csrf_token(
    html: str,
) -> str:
    parser = CsrfInputParser()
    parser.feed(html)

    assert parser.token is not None

    return parser.token


def obtain_login_csrf(
    client: TestClient,
) -> str:
    response = client.get(
        "/auth/login"
    )

    assert response.status_code == 200

    return extract_csrf_token(
        response.text
    )


def submit_login(
    client: TestClient,
    csrf_token: str,
):
    return client.post(
        "/auth/login",
        data={
            "csrf_token": csrf_token,
            "email": "operator@example.com",
            "password": "valid-password",
        },
        follow_redirects=False,
    )


def set_test_cookie(
    client: TestClient,
    *,
    name: str,
    value: str,
) -> None:
    """
    Insert a cookie into the HTTPX test cookie jar.

    The application still creates production cookies with
    Secure, HttpOnly and SameSite attributes. HTTPX's Cookies
    helper does not accept a `secure` keyword.
    """
    client.cookies.set(
        name,
        value,
        path="/",
    )


def test_successful_login_registers_session_before_redirect(
) -> None:
    registry = StubSessionRegistry()

    client = build_client(
        registry
    )

    csrf_token = obtain_login_csrf(
        client
    )

    response = submit_login(
        client,
        csrf_token,
    )

    assert response.status_code == 303

    assert response.headers["location"] == (
        "/patent-readiness/dashboard"
    )

    assert len(
        registry.register_calls
    ) == 1

    session_cookie = response.cookies.get(
        SESSION_COOKIE_NAME
    )

    assert session_cookie is not None

    decoded = decode_browser_session_token(
        session_cookie
    )

    assert decoded is not None

    assert (
        registry.register_calls[0][0].token_id
        == decoded.token_id
    )

    assert (
        registry.register_calls[0][1]
        == "default"
    )


def test_registration_failure_does_not_issue_session_cookie(
) -> None:
    registry = StubSessionRegistry(
        register_error=(
            BrowserSessionRecordConflictError(
                "Session registration failed."
            )
        )
    )

    client = build_client(
        registry
    )

    csrf_token = obtain_login_csrf(
        client
    )

    response = submit_login(
        client,
        csrf_token,
    )

    assert response.status_code == 503

    assert (
        "Authentication could not be completed"
        in response.text
    )

    assert (
        response.cookies.get(
            SESSION_COOKIE_NAME
        )
        is None
    )


def test_active_existing_session_redirects_from_login(
) -> None:
    registry = StubSessionRegistry()

    client = build_client(
        registry
    )

    token = issue_browser_session_token(
        build_account()
    )

    set_test_cookie(
        client,
        name=SESSION_COOKIE_NAME,
        value=token,
    )

    response = client.get(
        "/auth/login",
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers["location"] == (
        "/patent-readiness/dashboard"
    )

    assert len(
        registry.require_active_calls
    ) == 1


def test_inactive_existing_session_renders_login_and_clears_cookie(
) -> None:
    registry = StubSessionRegistry(
        require_active_error=(
            BrowserSessionRevokedError(
                "Browser session is revoked."
            )
        )
    )

    client = build_client(
        registry
    )

    token = issue_browser_session_token(
        build_account()
    )

    set_test_cookie(
        client,
        name=SESSION_COOKIE_NAME,
        value=token,
    )

    response = client.get(
        "/auth/login",
        follow_redirects=False,
    )

    assert response.status_code == 200

    assert len(
        registry.require_active_calls
    ) == 1

    set_cookie_header = (
        response.headers.get(
            "set-cookie",
            "",
        )
    )

    assert SESSION_COOKIE_NAME in (
        set_cookie_header
    )

    assert "Max-Age=0" in (
        set_cookie_header
    )


def test_logout_revokes_current_session(
) -> None:
    registry = StubSessionRegistry()

    client = build_client(
        registry
    )

    session_token = (
        issue_browser_session_token(
            build_account()
        )
    )

    csrf_token = (
        issue_browser_csrf_token()
    )

    set_test_cookie(
        client,
        name=SESSION_COOKIE_NAME,
        value=session_token,
    )

    set_test_cookie(
        client,
        name=CSRF_COOKIE_NAME,
        value=csrf_token,
    )

    response = client.post(
        "/auth/logout",
        data={
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers["location"] == (
        "/auth/login"
    )

    assert len(
        registry.revoke_calls
    ) == 1

    identity, reason, revoker = (
        registry.revoke_calls[0]
    )

    assert reason == "logout"
    assert revoker == identity.user_id


@pytest.mark.parametrize(
    "registry_error",
    [
        BrowserSessionNotRegisteredError(
            "Session is not registered."
        ),
        BrowserSessionRevokedError(
            "Session is already revoked."
        ),
    ],
)
def test_logout_is_idempotent_for_inactive_session(
    registry_error: BrowserSessionRegistryError,
) -> None:
    registry = StubSessionRegistry(
        revoke_error=registry_error
    )

    client = build_client(
        registry
    )

    session_token = (
        issue_browser_session_token(
            build_account()
        )
    )

    csrf_token = (
        issue_browser_csrf_token()
    )

    set_test_cookie(
        client,
        name=SESSION_COOKIE_NAME,
        value=session_token,
    )

    set_test_cookie(
        client,
        name=CSRF_COOKIE_NAME,
        value=csrf_token,
    )

    response = client.post(
        "/auth/logout",
        data={
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers["location"] == (
        "/auth/login"
    )

    assert len(
        registry.revoke_calls
    ) == 1


def test_logout_registry_failure_returns_503_and_clears_cookie(
) -> None:
    registry = StubSessionRegistry(
        revoke_error=(
            BrowserSessionRecordConflictError(
                "Registry unavailable."
            )
        )
    )

    client = build_client(
        registry
    )

    session_token = (
        issue_browser_session_token(
            build_account()
        )
    )

    csrf_token = (
        issue_browser_csrf_token()
    )

    set_test_cookie(
        client,
        name=SESSION_COOKIE_NAME,
        value=session_token,
    )

    set_test_cookie(
        client,
        name=CSRF_COOKIE_NAME,
        value=csrf_token,
    )

    response = client.post(
        "/auth/logout",
        data={
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 503

    assert (
        "Logout could not be completed"
        in response.text
    )

    assert len(
        registry.revoke_calls
    ) == 1

    set_cookie_header = (
        response.headers.get(
            "set-cookie",
            "",
        )
    )

    assert SESSION_COOKIE_NAME in (
        set_cookie_header
    )

    assert "Max-Age=0" in (
        set_cookie_header
    )