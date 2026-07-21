from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import Request, Response

from app.services.auth.browser_session import (
    BrowserSessionConfigurationError,
    BrowserSessionSettings,
    clear_browser_session_cookie,
    decode_browser_session_token,
    get_browser_session_settings,
    get_browser_session_token,
    issue_browser_session_token,
    set_browser_session_cookie,
)
from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.jwt_handler import (
    create_access_token,
)


TEST_JWT_SECRET = (
    "cgms-browser-session-test-secret-with-more-than-32-characters"
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
        "cgms-browser-session-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-browser-dashboard-test",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        "__Host-cgms_session",
    )

    monkeypatch.setenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        "30",
    )


def build_account(
    *,
    user_id: int = 1001,
    role: str = "admin",
    stored_role: str | None = None,
    used_legacy_alias: bool = False,
) -> AuthenticatedAccount:
    return AuthenticatedAccount(
        user_id=user_id,
        email="user@example.com",
        stored_role=(
            stored_role
            if stored_role is not None
            else role
        ),
        canonical_role=role,
        used_legacy_alias=used_legacy_alias,
    )


def build_request_with_cookie(
    *,
    cookie_name: str,
    cookie_value: str,
) -> Request:
    cookie_header = (
        f"{cookie_name}={cookie_value}"
    ).encode("latin-1")

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (
                    b"cookie",
                    cookie_header,
                )
            ],
            "query_string": b"",
            "server": (
                "testserver",
                443,
            ),
            "client": (
                "127.0.0.1",
                12345,
            ),
            "scheme": "https",
        }
    )


def test_default_session_settings_are_hardened() -> None:
    settings = get_browser_session_settings()

    assert (
        settings.cookie_name
        == "__Host-cgms_session"
    )

    assert settings.expire_minutes == 30
    assert settings.max_age_seconds == 1800
    assert settings.secure is True
    assert settings.httponly is True
    assert settings.samesite == "strict"
    assert settings.path == "/"


@pytest.mark.parametrize(
    "cookie_name",
    [
        "cgms_session",
        "__Secure-cgms_session",
        "__Host-cgms session",
        "__Host-",
        "",
    ],
)
def test_invalid_cookie_names_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    cookie_name: str,
) -> None:
    monkeypatch.setenv(
        "CGMS_SESSION_COOKIE_NAME",
        cookie_name,
    )

    with pytest.raises(
        BrowserSessionConfigurationError,
        match="__Host-",
    ):
        get_browser_session_settings()


@pytest.mark.parametrize(
    "expiry",
    [
        "not-an-integer",
        "0",
        "4",
        "1441",
        "-10",
    ],
)
def test_invalid_session_expiry_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    expiry: str,
) -> None:
    monkeypatch.setenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        expiry,
    )

    with pytest.raises(
        BrowserSessionConfigurationError,
        match="CGMS_SESSION_EXPIRE_MINUTES",
    ):
        get_browser_session_settings()


def test_issues_and_decodes_browser_session() -> None:
    account = build_account(
        role="operator"
    )

    token = issue_browser_session_token(
        account
    )

    identity = decode_browser_session_token(
        token
    )

    assert identity is not None
    assert identity.user_id == "1001"
    assert identity.role == "operator"
    assert identity.token_id
    assert identity.expires_at > identity.issued_at
    assert identity.is_expired is False

    lifetime = (
        identity.expires_at
        - identity.issued_at
    )

    assert lifetime == timedelta(
        minutes=30
    )


def test_legacy_account_role_is_issued_canonically() -> None:
    account = build_account(
        role="operator",
        stored_role="contributor",
        used_legacy_alias=True,
    )

    token = issue_browser_session_token(
        account
    )

    identity = decode_browser_session_token(
        token
    )

    assert identity is not None
    assert identity.role == "operator"


def test_ordinary_access_token_is_not_browser_session() -> None:
    token = create_access_token(
        {
            "user_id": "1001",
            "role": "admin",
        }
    )

    assert (
        decode_browser_session_token(token)
        is None
    )


def test_token_with_wrong_use_is_rejected() -> None:
    token = create_access_token(
        {
            "user_id": "1001",
            "role": "admin",
            "token_use": "password_reset",
        }
    )

    assert (
        decode_browser_session_token(token)
        is None
    )


def test_invalid_token_is_rejected() -> None:
    assert (
        decode_browser_session_token(
            "not-a-valid-token"
        )
        is None
    )


def test_token_signed_with_different_secret_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = issue_browser_session_token(
        build_account()
    )

    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        (
            "different-browser-session-secret-"
            "with-more-than-32-characters"
        ),
    )

    assert (
        decode_browser_session_token(token)
        is None
    )


def test_session_cookie_uses_required_security_attributes() -> None:
    token = issue_browser_session_token(
        build_account(
            role="operator"
        )
    )

    response = Response()

    identity = set_browser_session_cookie(
        response,
        token,
    )

    assert identity.role == "operator"

    cookie_header = response.headers[
        "set-cookie"
    ]

    normalized_header = cookie_header.lower()

    assert (
        "__Host-cgms_session="
        in cookie_header
    )

    assert "path=/" in normalized_header
    assert "secure" in normalized_header
    assert "httponly" in normalized_header
    assert "samesite=strict" in normalized_header
    assert "max-age=" in normalized_header
    assert "expires=" in normalized_header
    assert "domain=" not in normalized_header


def test_invalid_token_cannot_be_set_as_cookie() -> None:
    response = Response()

    with pytest.raises(
        ValueError,
        match="invalid browser-session token",
    ):
        set_browser_session_cookie(
            response,
            "invalid-token",
        )


def test_clear_session_cookie_preserves_security_attributes() -> None:
    response = Response()

    clear_browser_session_cookie(
        response
    )

    cookie_header = response.headers[
        "set-cookie"
    ]

    normalized_header = cookie_header.lower()

    assert (
        "__Host-cgms_session="
        in cookie_header
    )

    assert "max-age=0" in normalized_header
    assert "path=/" in normalized_header
    assert "secure" in normalized_header
    assert "httponly" in normalized_header
    assert "samesite=strict" in normalized_header
    assert "domain=" not in normalized_header


def test_get_session_token_from_request_cookie() -> None:
    token = issue_browser_session_token(
        build_account()
    )

    request = build_request_with_cookie(
        cookie_name="__Host-cgms_session",
        cookie_value=token,
    )

    assert (
        get_browser_session_token(request)
        == token
    )


def test_missing_session_cookie_returns_none() -> None:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "server": (
                "testserver",
                443,
            ),
            "client": (
                "127.0.0.1",
                12345,
            ),
            "scheme": "https",
        }
    )

    assert (
        get_browser_session_token(request)
        is None
    )


def test_custom_valid_host_cookie_name_is_supported() -> None:
    settings = BrowserSessionSettings(
        cookie_name=(
            "__Host-cgms_patent_session"
        ),
        expire_minutes=15,
    )

    token = issue_browser_session_token(
        build_account(),
        settings=settings,
    )

    response = Response()

    set_browser_session_cookie(
        response,
        token,
        settings=settings,
    )

    assert (
        "__Host-cgms_patent_session="
        in response.headers["set-cookie"]
    )

    request = build_request_with_cookie(
        cookie_name=(
            "__Host-cgms_patent_session"
        ),
        cookie_value=token,
    )

    assert (
        get_browser_session_token(
            request,
            settings=settings,
        )
        == token
    )