from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response


DEFAULT_CSRF_COOKIE_NAME = "__Host-cgms_csrf"
DEFAULT_CSRF_EXPIRE_SECONDS = 600

CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_SAMESITE = "strict"
CSRF_TOKEN_VERSION = "v1"
CSRF_TOKEN_CONTEXT = "cgms-browser-csrf"
CSRF_MAX_CLOCK_SKEW_SECONDS = 60

_COOKIE_NAME_PATTERN = re.compile(
    r"^__Host-[A-Za-z0-9._-]+$"
)


class BrowserCsrfConfigurationError(
    RuntimeError
):
    """
    Raised when browser-CSRF configuration is invalid or
    insecure.
    """


class BrowserCsrfValidationError(
    ValueError
):
    """
    Raised when a submitted browser-CSRF token cannot be
    validated.

    The public message is deliberately generic.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class BrowserCsrfSettings:
    cookie_name: str
    expire_seconds: int

    @property
    def secure(self) -> bool:
        return True

    @property
    def httponly(self) -> bool:
        return True

    @property
    def samesite(self) -> str:
        return CSRF_COOKIE_SAMESITE

    @property
    def path(self) -> str:
        return CSRF_COOKIE_PATH


@dataclass(
    frozen=True,
    slots=True,
)
class BrowserCsrfIdentity:
    issued_at: datetime
    expires_at: datetime
    nonce: str

    @property
    def is_expired(self) -> bool:
        return (
            self.expires_at
            <= datetime.now(timezone.utc)
        )


def get_browser_csrf_settings(
) -> BrowserCsrfSettings:
    cookie_name = os.getenv(
        "CGMS_CSRF_COOKIE_NAME",
        DEFAULT_CSRF_COOKIE_NAME,
    ).strip()

    if not _COOKIE_NAME_PATTERN.fullmatch(
        cookie_name
    ):
        raise BrowserCsrfConfigurationError(
            "CGMS_CSRF_COOKIE_NAME must use the "
            "__Host- prefix and contain only letters, "
            "numbers, periods, underscores or hyphens."
        )

    raw_expiry = os.getenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        str(DEFAULT_CSRF_EXPIRE_SECONDS),
    ).strip()

    try:
        expire_seconds = int(raw_expiry)
    except (TypeError, ValueError) as exc:
        raise BrowserCsrfConfigurationError(
            "CGMS_CSRF_EXPIRE_SECONDS must be "
            "an integer."
        ) from exc

    if not 120 <= expire_seconds <= 3600:
        raise BrowserCsrfConfigurationError(
            "CGMS_CSRF_EXPIRE_SECONDS must be "
            "between 120 and 3600 seconds."
        )

    return BrowserCsrfSettings(
        cookie_name=cookie_name,
        expire_seconds=expire_seconds,
    )


def _get_csrf_secret() -> bytes:
    secret = os.getenv(
        "CGMS_JWT_SECRET",
        "",
    )

    if len(secret) < 32:
        raise BrowserCsrfConfigurationError(
            "CGMS_JWT_SECRET must contain at least "
            "32 characters before browser CSRF "
            "protection can be used."
        )

    return secret.encode("utf-8")


def _current_time(
    supplied_time: datetime | None,
) -> datetime:
    current = (
        supplied_time
        if supplied_time is not None
        else datetime.now(timezone.utc)
    )

    if current.tzinfo is None:
        current = current.replace(
            tzinfo=timezone.utc
        )

    return current.astimezone(
        timezone.utc
    )


def _build_unsigned_token(
    *,
    issued_at: int,
    nonce: str,
) -> str:
    return (
        f"{CSRF_TOKEN_VERSION}."
        f"{issued_at}."
        f"{nonce}"
    )


def _sign_unsigned_token(
    unsigned_token: str,
) -> str:
    message = (
        f"{CSRF_TOKEN_CONTEXT}:"
        f"{unsigned_token}"
    ).encode("utf-8")

    return hmac.new(
        _get_csrf_secret(),
        message,
        hashlib.sha256,
    ).hexdigest()


def issue_browser_csrf_token(
    *,
    now: datetime | None = None,
) -> str:
    """
    Issue a signed, time-limited double-submit CSRF token.

    The same signed value is rendered into the HTML form and
    stored in a host-bound HttpOnly cookie.
    """
    current = _current_time(now)
    issued_at = int(current.timestamp())
    nonce = secrets.token_urlsafe(32)

    unsigned_token = _build_unsigned_token(
        issued_at=issued_at,
        nonce=nonce,
    )

    signature = _sign_unsigned_token(
        unsigned_token
    )

    return (
        f"{unsigned_token}."
        f"{signature}"
    )


def decode_browser_csrf_token(
    token: str,
    *,
    settings: BrowserCsrfSettings | None = None,
    now: datetime | None = None,
) -> BrowserCsrfIdentity | None:
    if not isinstance(token, str):
        return None

    normalized_token = token.strip()

    if not normalized_token:
        return None

    parts = normalized_token.split(".")

    if len(parts) != 4:
        return None

    version, raw_issued_at, nonce, signature = (
        parts
    )

    if version != CSRF_TOKEN_VERSION:
        return None

    if (
        not nonce
        or len(nonce) < 32
        or len(signature) != 64
    ):
        return None

    try:
        issued_at_timestamp = int(
            raw_issued_at
        )
    except (TypeError, ValueError):
        return None

    unsigned_token = _build_unsigned_token(
        issued_at=issued_at_timestamp,
        nonce=nonce,
    )

    expected_signature = (
        _sign_unsigned_token(
            unsigned_token
        )
    )

    if not hmac.compare_digest(
        signature,
        expected_signature,
    ):
        return None

    resolved_settings = (
        settings
        if settings is not None
        else get_browser_csrf_settings()
    )

    current = _current_time(now)

    try:
        issued_at = datetime.fromtimestamp(
            issued_at_timestamp,
            tz=timezone.utc,
        )
    except (
        OverflowError,
        OSError,
        ValueError,
    ):
        return None

    if issued_at > (
        current
        + timedelta(
            seconds=CSRF_MAX_CLOCK_SKEW_SECONDS
        )
    ):
        return None

    expires_at = (
        issued_at
        + timedelta(
            seconds=(
                resolved_settings
                .expire_seconds
            )
        )
    )

    if expires_at <= current:
        return None

    return BrowserCsrfIdentity(
        issued_at=issued_at,
        expires_at=expires_at,
        nonce=nonce,
    )


def validate_browser_csrf_tokens(
    *,
    submitted_token: str | None,
    cookie_token: str | None,
    settings: BrowserCsrfSettings | None = None,
    now: datetime | None = None,
) -> BrowserCsrfIdentity:
    """
    Validate the double-submit token pair and its signature,
    timestamp and expiry.
    """
    if (
        not isinstance(submitted_token, str)
        or not isinstance(cookie_token, str)
        or not submitted_token.strip()
        or not cookie_token.strip()
    ):
        raise BrowserCsrfValidationError(
            "Invalid or expired CSRF token."
        )

    normalized_submitted = (
        submitted_token.strip()
    )

    normalized_cookie = (
        cookie_token.strip()
    )

    if not hmac.compare_digest(
        normalized_submitted,
        normalized_cookie,
    ):
        raise BrowserCsrfValidationError(
            "Invalid or expired CSRF token."
        )

    identity = decode_browser_csrf_token(
        normalized_submitted,
        settings=settings,
        now=now,
    )

    if identity is None:
        raise BrowserCsrfValidationError(
            "Invalid or expired CSRF token."
        )

    return identity


def set_browser_csrf_cookie(
    response: Response,
    token: str,
    *,
    settings: BrowserCsrfSettings | None = None,
) -> BrowserCsrfIdentity:
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_csrf_settings()
    )

    identity = decode_browser_csrf_token(
        token,
        settings=resolved_settings,
    )

    if identity is None:
        raise ValueError(
            "Cannot set an invalid browser-CSRF token."
        )

    remaining_seconds = max(
        0,
        int(
            (
                identity.expires_at
                - datetime.now(timezone.utc)
            ).total_seconds()
        ),
    )

    response.set_cookie(
        key=resolved_settings.cookie_name,
        value=token,
        max_age=remaining_seconds,
        expires=identity.expires_at,
        path=resolved_settings.path,
        secure=resolved_settings.secure,
        httponly=resolved_settings.httponly,
        samesite=resolved_settings.samesite,
    )

    return identity


def clear_browser_csrf_cookie(
    response: Response,
    *,
    settings: BrowserCsrfSettings | None = None,
) -> None:
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_csrf_settings()
    )

    response.delete_cookie(
        key=resolved_settings.cookie_name,
        path=resolved_settings.path,
        secure=resolved_settings.secure,
        httponly=resolved_settings.httponly,
        samesite=resolved_settings.samesite,
    )


def get_browser_csrf_cookie(
    request: Request,
    *,
    settings: BrowserCsrfSettings | None = None,
) -> str | None:
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_csrf_settings()
    )

    token = request.cookies.get(
        resolved_settings.cookie_name
    )

    if not isinstance(token, str):
        return None

    normalized_token = token.strip()

    return normalized_token or None


def validate_browser_csrf_request(
    request: Request,
    *,
    submitted_token: str | None,
    settings: BrowserCsrfSettings | None = None,
) -> BrowserCsrfIdentity:
    return validate_browser_csrf_tokens(
        submitted_token=submitted_token,
        cookie_token=get_browser_csrf_cookie(
            request,
            settings=settings,
        ),
        settings=settings,
    )