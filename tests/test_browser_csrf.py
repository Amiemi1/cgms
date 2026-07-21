from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Request, Response

from app.services.auth.browser_csrf import (
    BrowserCsrfConfigurationError,
    BrowserCsrfSettings,
    BrowserCsrfValidationError,
    clear_browser_csrf_cookie,
    decode_browser_csrf_token,
    get_browser_csrf_cookie,
    get_browser_csrf_settings,
    issue_browser_csrf_token,
    set_browser_csrf_cookie,
    validate_browser_csrf_request,
    validate_browser_csrf_tokens,
)


TEST_JWT_SECRET = (
    "cgms-browser-csrf-test-secret-"
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
        "CGMS_CSRF_COOKIE_NAME",
        "__Host-cgms_csrf",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        "600",
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
            "method": "POST",
            "path": "/auth/login",
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


def build_request_without_cookie() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/auth/login",
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


def test_default_csrf_settings_are_hardened() -> None:
    settings = get_browser_csrf_settings()

    assert settings.cookie_name == (
        "__Host-cgms_csrf"
    )

    assert settings.expire_seconds == 600
    assert settings.secure is True
    assert settings.httponly is True
    assert settings.samesite == "strict"
    assert settings.path == "/"


@pytest.mark.parametrize(
    "cookie_name",
    [
        "cgms_csrf",
        "__Secure-cgms_csrf",
        "__Host-cgms csrf",
        "__Host-",
        "",
    ],
)
def test_invalid_cookie_names_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    cookie_name: str,
) -> None:
    monkeypatch.setenv(
        "CGMS_CSRF_COOKIE_NAME",
        cookie_name,
    )

    with pytest.raises(
        BrowserCsrfConfigurationError,
        match="__Host-",
    ):
        get_browser_csrf_settings()


@pytest.mark.parametrize(
    "expiry",
    [
        "not-an-integer",
        "0",
        "119",
        "3601",
        "-100",
    ],
)
def test_invalid_expiry_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    expiry: str,
) -> None:
    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        expiry,
    )

    with pytest.raises(
        BrowserCsrfConfigurationError,
        match="CGMS_CSRF_EXPIRE_SECONDS",
    ):
        get_browser_csrf_settings()


@pytest.mark.parametrize(
    "secret",
    [
        "",
        "short",
        "fewer-than-thirty-two-chars",
    ],
)
def test_short_signing_secret_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    secret: str,
) -> None:
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        secret,
    )

    with pytest.raises(
        BrowserCsrfConfigurationError,
        match="at least 32 characters",
    ):
        issue_browser_csrf_token()


def test_issues_and_decodes_csrf_token() -> None:
    now = datetime.now(timezone.utc)

    token = issue_browser_csrf_token(
        now=now
    )

    identity = decode_browser_csrf_token(
        token,
        now=now,
    )

    assert identity is not None
    assert identity.issued_at == (
        now.replace(microsecond=0)
    )

    assert identity.expires_at == (
        identity.issued_at
        + timedelta(seconds=600)
    )

    assert len(identity.nonce) >= 32


def test_each_issued_token_has_unique_nonce() -> None:
    now = datetime.now(timezone.utc)

    first_token = issue_browser_csrf_token(
        now=now
    )

    second_token = issue_browser_csrf_token(
        now=now
    )

    assert first_token != second_token


def test_token_is_valid_before_expiry() -> None:
    issued_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    token = issue_browser_csrf_token(
        now=issued_at
    )

    identity = decode_browser_csrf_token(
        token,
        now=(
            issued_at
            + timedelta(seconds=599)
        ),
    )

    assert identity is not None


def test_token_is_invalid_at_expiry_boundary() -> None:
    issued_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    token = issue_browser_csrf_token(
        now=issued_at
    )

    identity = decode_browser_csrf_token(
        token,
        now=(
            issued_at
            + timedelta(seconds=600)
        ),
    )

    assert identity is None


def test_token_too_far_in_future_is_rejected() -> None:
    current = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    token = issue_browser_csrf_token(
        now=(
            current
            + timedelta(seconds=61)
        )
    )

    assert (
        decode_browser_csrf_token(
            token,
            now=current,
        )
        is None
    )


def test_token_within_clock_skew_is_accepted() -> None:
    current = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    token = issue_browser_csrf_token(
        now=(
            current
            + timedelta(seconds=60)
        )
    )

    assert (
        decode_browser_csrf_token(
            token,
            now=current,
        )
        is not None
    )


@pytest.mark.parametrize(
    "token",
    [
        "",
        " ",
        "invalid",
        "v1.invalid",
        "v2.123.nonce.signature",
        "v1.not-a-number.nonce.signature",
    ],
)
def test_malformed_tokens_are_rejected(
    token: str,
) -> None:
    assert (
        decode_browser_csrf_token(token)
        is None
    )


def test_tampered_nonce_is_rejected() -> None:
    token = issue_browser_csrf_token()

    parts = token.split(".")
    parts[2] = (
        "tampered-token-nonce-value-"
        "with-sufficient-length"
    )

    tampered_token = ".".join(parts)

    assert (
        decode_browser_csrf_token(
            tampered_token
        )
        is None
    )


def test_tampered_signature_is_rejected() -> None:
    token = issue_browser_csrf_token()

    parts = token.split(".")
    parts[3] = "0" * 64

    tampered_token = ".".join(parts)

    assert (
        decode_browser_csrf_token(
            tampered_token
        )
        is None
    )


def test_token_signed_with_different_secret_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = issue_browser_csrf_token()

    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        (
            "different-cgms-browser-csrf-secret-"
            "with-more-than-32-characters"
        ),
    )

    assert (
        decode_browser_csrf_token(token)
        is None
    )


def test_matching_tokens_are_validated() -> None:
    now = datetime.now(timezone.utc)

    token = issue_browser_csrf_token(
        now=now
    )

    identity = validate_browser_csrf_tokens(
        submitted_token=token,
        cookie_token=token,
        now=now,
    )

    assert identity.nonce


@pytest.mark.parametrize(
    ("submitted_token", "cookie_token"),
    [
        (None, None),
        ("", ""),
        (" ", " "),
        ("submitted-token", None),
        (None, "cookie-token"),
    ],
)
def test_missing_tokens_fail_validation(
    submitted_token: str | None,
    cookie_token: str | None,
) -> None:
    with pytest.raises(
        BrowserCsrfValidationError,
        match="Invalid or expired CSRF token",
    ):
        validate_browser_csrf_tokens(
            submitted_token=submitted_token,
            cookie_token=cookie_token,
        )


def test_mismatched_tokens_fail_validation() -> None:
    first_token = issue_browser_csrf_token()
    second_token = issue_browser_csrf_token()

    with pytest.raises(
        BrowserCsrfValidationError,
        match="Invalid or expired CSRF token",
    ):
        validate_browser_csrf_tokens(
            submitted_token=first_token,
            cookie_token=second_token,
        )


def test_expired_matching_tokens_fail_validation() -> None:
    issued_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=timezone.utc,
    )

    token = issue_browser_csrf_token(
        now=issued_at
    )

    with pytest.raises(
        BrowserCsrfValidationError,
        match="Invalid or expired CSRF token",
    ):
        validate_browser_csrf_tokens(
            submitted_token=token,
            cookie_token=token,
            now=(
                issued_at
                + timedelta(seconds=600)
            ),
        )


def test_csrf_cookie_uses_required_security_attributes() -> None:
    token = issue_browser_csrf_token()

    response = Response()

    identity = set_browser_csrf_cookie(
        response,
        token,
    )

    assert identity.nonce

    cookie_header = response.headers[
        "set-cookie"
    ]

    normalized_header = cookie_header.lower()

    assert (
        "__Host-cgms_csrf="
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
        match="invalid browser-CSRF token",
    ):
        set_browser_csrf_cookie(
            response,
            "invalid-token",
        )


def test_clear_csrf_cookie_preserves_security_attributes() -> None:
    response = Response()

    clear_browser_csrf_cookie(
        response
    )

    cookie_header = response.headers[
        "set-cookie"
    ]

    normalized_header = cookie_header.lower()

    assert (
        "__Host-cgms_csrf="
        in cookie_header
    )

    assert "max-age=0" in normalized_header
    assert "path=/" in normalized_header
    assert "secure" in normalized_header
    assert "httponly" in normalized_header
    assert "samesite=strict" in normalized_header
    assert "domain=" not in normalized_header


def test_get_csrf_cookie_from_request() -> None:
    token = issue_browser_csrf_token()

    request = build_request_with_cookie(
        cookie_name="__Host-cgms_csrf",
        cookie_value=token,
    )

    assert (
        get_browser_csrf_cookie(request)
        == token
    )


def test_missing_csrf_cookie_returns_none() -> None:
    assert (
        get_browser_csrf_cookie(
            build_request_without_cookie()
        )
        is None
    )


def test_validates_csrf_request_pair() -> None:
    token = issue_browser_csrf_token()

    request = build_request_with_cookie(
        cookie_name="__Host-cgms_csrf",
        cookie_value=token,
    )

    identity = validate_browser_csrf_request(
        request,
        submitted_token=token,
    )

    assert identity.nonce


def test_request_without_cookie_fails_validation() -> None:
    token = issue_browser_csrf_token()

    with pytest.raises(
        BrowserCsrfValidationError,
        match="Invalid or expired CSRF token",
    ):
        validate_browser_csrf_request(
            build_request_without_cookie(),
            submitted_token=token,
        )


def test_custom_valid_cookie_name_is_supported() -> None:
    settings = BrowserCsrfSettings(
        cookie_name=(
            "__Host-cgms_login_csrf"
        ),
        expire_seconds=300,
    )

    token = issue_browser_csrf_token()

    response = Response()

    set_browser_csrf_cookie(
        response,
        token,
        settings=settings,
    )

    assert (
        "__Host-cgms_login_csrf="
        in response.headers["set-cookie"]
    )

    request = build_request_with_cookie(
        cookie_name=(
            "__Host-cgms_login_csrf"
        ),
        cookie_value=token,
    )

    assert (
        get_browser_csrf_cookie(
            request,
            settings=settings,
        )
        == token
    )