from __future__ import annotations

import html
import re
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.routes.browser_auth import (
    AUTHENTICATED_REDIRECT_PATH,
    GENERIC_LOGIN_ERROR,
    GENERIC_REQUEST_ERROR,
    LOGIN_PATH,
    MAX_FORM_BODY_BYTES,
    get_credential_authentication_service,
    router,
)
from app.services.auth.browser_csrf import (
    issue_browser_csrf_token,
)
from app.services.auth.browser_session import (
    issue_browser_session_token,
)
from app.services.auth.credential_service import (
    AccountRoleConfigurationError,
    AuthenticatedAccount,
    InvalidCredentialsError,
)


TEST_JWT_SECRET = (
    "cgms-browser-auth-route-test-secret-"
    "with-more-than-32-characters"
)

TEST_PASSWORD = (
    "Correct-Horse-Battery-Staple-2026!"
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
        "cgms-browser-auth-route-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-browser-auth-dashboard-test",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        "__Host-cgms_session",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        "30",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_COOKIE_NAME",
        "__Host-cgms_csrf",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        "600",
    )


class StubCredentialService:
    def __init__(
        self,
        *,
        account: AuthenticatedAccount | None = None,
        error: Exception | None = None,
    ) -> None:
        self.account = account
        self.error = error
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

        if self.error is not None:
            raise self.error

        if self.account is None:
            raise AssertionError(
                "No authentication result configured."
            )

        return self.account


def build_account(
    *,
    user_id: int = 1001,
    role: str = "operator",
) -> AuthenticatedAccount:
    return AuthenticatedAccount(
        user_id=user_id,
        email="user@example.com",
        stored_role=role,
        canonical_role=role,
        used_legacy_alias=False,
    )


def build_client(
    credential_service: StubCredentialService,
) -> TestClient:
    app = FastAPI()

    app.include_router(
        router
    )

    app.dependency_overrides[
        get_credential_authentication_service
    ] = lambda: credential_service

    return TestClient(
        app,
        base_url="https://testserver",
    )


def extract_csrf_token(
    response,
) -> str:
    match = re.search(
        (
            r'name="csrf_token"'
            r'\s+value="([^"]+)"'
        ),
        response.text,
    )

    assert match is not None

    return html.unescape(
        match.group(1)
    )


def get_set_cookie_headers(
    response,
) -> list[str]:
    return response.headers.get_list(
        "set-cookie"
    )


def assert_security_headers(
    response,
) -> None:
    assert response.headers[
        "cache-control"
    ] == "no-store, max-age=0"

    assert response.headers[
        "pragma"
    ] == "no-cache"

    assert response.headers[
        "x-content-type-options"
    ] == "nosniff"

    assert response.headers[
        "x-frame-options"
    ] == "DENY"

    assert response.headers[
        "referrer-policy"
    ] == "no-referrer"

    assert response.headers[
        "cross-origin-opener-policy"
    ] == "same-origin"

    content_security_policy = (
        response.headers[
            "content-security-policy"
        ]
    )

    assert "default-src 'none'" in (
        content_security_policy
    )

    assert "form-action 'self'" in (
        content_security_policy
    )

    assert "frame-ancestors 'none'" in (
        content_security_policy
    )


def test_login_page_issues_csrf_cookie_and_form() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    response = client.get(
        LOGIN_PATH,
        follow_redirects=False,
    )

    assert response.status_code == 200

    assert (
        "<title>CGMS Secure Sign In</title>"
        in response.text
    )

    assert (
        'action="/auth/login"'
        in response.text
    )

    csrf_token = extract_csrf_token(
        response
    )

    assert csrf_token
    assert TEST_PASSWORD not in response.text

    cookies = get_set_cookie_headers(
        response
    )

    csrf_cookie = next(
        cookie
        for cookie in cookies
        if (
            "__Host-cgms_csrf="
            in cookie
        )
    )

    normalized_cookie = (
        csrf_cookie.lower()
    )

    assert "secure" in normalized_cookie
    assert "httponly" in normalized_cookie
    assert "samesite=strict" in normalized_cookie
    assert "path=/" in normalized_cookie
    assert "domain=" not in normalized_cookie

    assert_security_headers(response)
    assert service.calls == []


def test_authenticated_user_is_redirected_from_login_page() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    session_token = (
        issue_browser_session_token(
            build_account(
                user_id=2001,
                role="admin",
            )
        )
    )

    response = client.get(
        LOGIN_PATH,
        headers={
            "Cookie": (
                "__Host-cgms_session="
                f"{session_token}"
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers[
        "location"
    ] == AUTHENTICATED_REDIRECT_PATH

    assert_security_headers(response)
    assert service.calls == []


def test_valid_login_sets_secure_session_cookie() -> None:
    account = build_account(
        user_id=3001,
        role="operator",
    )

    service = StubCredentialService(
        account=account
    )

    client = build_client(service)

    login_page = client.get(
        LOGIN_PATH
    )

    csrf_token = extract_csrf_token(
        login_page
    )

    response = client.post(
        LOGIN_PATH,
        data={
            "csrf_token": csrf_token,
            "email": " User@Example.com ",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers[
        "location"
    ] == AUTHENTICATED_REDIRECT_PATH

    assert service.calls == [
        (
            " User@Example.com ",
            TEST_PASSWORD,
        )
    ]

    cookies = get_set_cookie_headers(
        response
    )

    session_cookie = next(
        cookie
        for cookie in cookies
        if (
            "__Host-cgms_session="
            in cookie
        )
    )

    normalized_session_cookie = (
        session_cookie.lower()
    )

    assert "secure" in normalized_session_cookie
    assert "httponly" in normalized_session_cookie
    assert "samesite=strict" in normalized_session_cookie
    assert "path=/" in normalized_session_cookie
    assert "domain=" not in normalized_session_cookie

    csrf_clear_cookie = next(
        cookie
        for cookie in cookies
        if (
            "__Host-cgms_csrf="
            in cookie
            and "max-age=0"
            in cookie.lower()
        )
    )

    assert csrf_clear_cookie

    assert "access_token" not in response.text
    assert TEST_PASSWORD not in response.text

    assert_security_headers(response)


def test_invalid_credentials_use_generic_error() -> None:
    service = StubCredentialService(
        error=InvalidCredentialsError(
            "Invalid email or password."
        )
    )

    client = build_client(service)

    login_page = client.get(
        LOGIN_PATH
    )

    csrf_token = extract_csrf_token(
        login_page
    )

    submitted_email = (
        "known-user@example.com"
    )

    submitted_password = (
        "incorrect-secret-value"
    )

    response = client.post(
        LOGIN_PATH,
        data={
            "csrf_token": csrf_token,
            "email": submitted_email,
            "password": submitted_password,
        },
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert GENERIC_LOGIN_ERROR in response.text

    assert submitted_email not in response.text
    assert submitted_password not in response.text

    assert (
        "User not found"
        not in response.text
    )

    assert (
        "Invalid password"
        not in response.text
    )

    assert len(service.calls) == 1
    assert_security_headers(response)


def test_role_configuration_failure_uses_generic_login_error() -> None:
    service = StubCredentialService(
        error=AccountRoleConfigurationError(
            "Conflicting role assignments."
        )
    )

    client = build_client(service)

    login_page = client.get(
        LOGIN_PATH
    )

    csrf_token = extract_csrf_token(
        login_page
    )

    response = client.post(
        LOGIN_PATH,
        data={
            "csrf_token": csrf_token,
            "email": "user@example.com",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert GENERIC_LOGIN_ERROR in response.text

    assert (
        "Conflicting role assignments"
        not in response.text
    )

    assert_security_headers(response)


def test_missing_csrf_cookie_is_rejected_before_authentication() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    response = client.post(
        LOGIN_PATH,
        data={
            "csrf_token": (
                issue_browser_csrf_token()
            ),
            "email": "user@example.com",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []

    assert_security_headers(response)


def test_mismatched_csrf_token_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    client.get(
        LOGIN_PATH
    )

    different_token = (
        issue_browser_csrf_token()
    )

    response = client.post(
        LOGIN_PATH,
        data={
            "csrf_token": different_token,
            "email": "user@example.com",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_json_login_request_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    response = build_client(
        service
    ).post(
        LOGIN_PATH,
        json={
            "email": "user@example.com",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_duplicate_email_field_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    login_page = client.get(
        LOGIN_PATH
    )

    csrf_token = extract_csrf_token(
        login_page
    )

    body = urlencode(
        [
            (
                "csrf_token",
                csrf_token,
            ),
            (
                "email",
                "first@example.com",
            ),
            (
                "email",
                "second@example.com",
            ),
            (
                "password",
                TEST_PASSWORD,
            ),
        ]
    )

    response = client.post(
        LOGIN_PATH,
        content=body,
        headers={
            "Content-Type": (
                "application/"
                "x-www-form-urlencoded"
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_oversized_form_body_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    oversized_body = (
        b"x"
        * (
            MAX_FORM_BODY_BYTES
            + 1
        )
    )

    response = build_client(
        service
    ).post(
        LOGIN_PATH,
        content=oversized_body,
        headers={
            "Content-Type": (
                "application/"
                "x-www-form-urlencoded"
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_invalid_utf8_form_body_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    response = build_client(
        service
    ).post(
        LOGIN_PATH,
        content=b"\xff\xfe\xfa",
        headers={
            "Content-Type": (
                "application/"
                "x-www-form-urlencoded"
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_excessive_form_fields_are_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    form_fields = [
        (
            f"field_{index}",
            "value",
        )
        for index in range(11)
    ]

    response = build_client(
        service
    ).post(
        LOGIN_PATH,
        content=urlencode(
            form_fields
        ),
        headers={
            "Content-Type": (
                "application/"
                "x-www-form-urlencoded"
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert GENERIC_REQUEST_ERROR in response.text
    assert service.calls == []


def test_valid_logout_clears_session_and_csrf_cookies() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    login_page = client.get(
        LOGIN_PATH
    )

    csrf_token = extract_csrf_token(
        login_page
    )

    response = client.post(
        "/auth/logout",
        data={
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == LOGIN_PATH

    cookies = get_set_cookie_headers(
        response
    )

    session_clear_cookie = next(
        cookie
        for cookie in cookies
        if (
            "__Host-cgms_session="
            in cookie
        )
    )

    csrf_clear_cookie = next(
        cookie
        for cookie in cookies
        if (
            "__Host-cgms_csrf="
            in cookie
        )
    )

    assert (
        "max-age=0"
        in session_clear_cookie.lower()
    )

    assert (
        "max-age=0"
        in csrf_clear_cookie.lower()
    )

    assert_security_headers(response)
    assert service.calls == []


def test_logout_with_invalid_csrf_is_rejected() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    response = build_client(
        service
    ).post(
        "/auth/logout",
        data={
            "csrf_token": (
                issue_browser_csrf_token()
            ),
        },
        follow_redirects=False,
    )

    assert response.status_code == 400

    assert (
        "The request could not be validated."
        in response.text
    )

    assert (
        response.headers.get("location")
        is None
    )

    assert_security_headers(response)


def test_logout_is_post_only() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    response = build_client(
        service
    ).get(
        "/auth/logout",
        follow_redirects=False,
    )

    assert response.status_code == 405


def test_public_signup_route_is_not_exposed() -> None:
    service = StubCredentialService(
        account=build_account()
    )

    client = build_client(service)

    get_response = client.get(
        "/auth/signup",
        follow_redirects=False,
    )

    post_response = client.post(
        "/auth/signup",
        json={
            "email": "new@example.com",
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404