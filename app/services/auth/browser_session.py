from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from app.services.auth.credential_service import (
    AuthenticatedAccount,
)
from app.services.auth.jwt_handler import (
    create_access_token,
    decode_access_token,
)
from app.services.security.canonical_roles import (
    CanonicalRoleResolutionError,
    canonical_role_name,
)


DEFAULT_SESSION_COOKIE_NAME = "__Host-cgms_session"
DEFAULT_SESSION_EXPIRE_MINUTES = 30

SESSION_TOKEN_USE = "browser_session"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SAMESITE = "strict"

_COOKIE_NAME_PATTERN = re.compile(
    r"^__Host-[A-Za-z0-9._-]+$"
)


class BrowserSessionConfigurationError(
    RuntimeError
):
    """
    Raised when browser-session configuration is insecure or
    invalid.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class BrowserSessionSettings:
    cookie_name: str
    expire_minutes: int

    @property
    def max_age_seconds(self) -> int:
        return self.expire_minutes * 60

    @property
    def secure(self) -> bool:
        return True

    @property
    def httponly(self) -> bool:
        return True

    @property
    def samesite(self) -> str:
        return SESSION_COOKIE_SAMESITE

    @property
    def path(self) -> str:
        return SESSION_COOKIE_PATH


@dataclass(
    frozen=True,
    slots=True,
)
class BrowserSessionIdentity:
    user_id: str
    role: str
    token_id: str
    issued_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return (
            self.expires_at
            <= datetime.now(timezone.utc)
        )


def get_browser_session_settings(
) -> BrowserSessionSettings:
    cookie_name = os.getenv(
        "CGMS_SESSION_COOKIE_NAME",
        DEFAULT_SESSION_COOKIE_NAME,
    ).strip()

    if not _COOKIE_NAME_PATTERN.fullmatch(
        cookie_name
    ):
        raise BrowserSessionConfigurationError(
            "CGMS_SESSION_COOKIE_NAME must use the "
            "__Host- prefix and contain only letters, "
            "numbers, periods, underscores or hyphens."
        )

    raw_expiry = os.getenv(
        "CGMS_SESSION_EXPIRE_MINUTES",
        str(DEFAULT_SESSION_EXPIRE_MINUTES),
    ).strip()

    try:
        expire_minutes = int(raw_expiry)
    except (TypeError, ValueError) as exc:
        raise BrowserSessionConfigurationError(
            "CGMS_SESSION_EXPIRE_MINUTES must be "
            "an integer."
        ) from exc

    if not 5 <= expire_minutes <= 1440:
        raise BrowserSessionConfigurationError(
            "CGMS_SESSION_EXPIRE_MINUTES must be "
            "between 5 and 1440 minutes."
        )

    return BrowserSessionSettings(
        cookie_name=cookie_name,
        expire_minutes=expire_minutes,
    )


def _timestamp_to_datetime(
    value: object,
) -> datetime | None:
    if not isinstance(
        value,
        (int, float),
    ):
        return None

    try:
        return datetime.fromtimestamp(
            value,
            tz=timezone.utc,
        )
    except (
        OverflowError,
        OSError,
        ValueError,
    ):
        return None


def issue_browser_session_token(
    account: AuthenticatedAccount,
    *,
    settings: BrowserSessionSettings | None = None,
) -> str:
    """
    Issue a signed JWT intended exclusively for the secure
    browser-session cookie.

    The email address and password are deliberately excluded
    from the token.
    """
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_session_settings()
    )

    try:
        canonical_role = canonical_role_name(
            account.canonical_role
        )
    except CanonicalRoleResolutionError as exc:
        raise BrowserSessionConfigurationError(
            "Cannot issue a session for an "
            "unrecognized account role."
        ) from exc

    return create_access_token(
        {
            "user_id": account.token_subject,
            "role": canonical_role,
            "token_use": SESSION_TOKEN_USE,
        },
        expires_delta=timedelta(
            minutes=(
                resolved_settings
                .expire_minutes
            )
        ),
    )


def decode_browser_session_token(
    token: str,
) -> BrowserSessionIdentity | None:
    """
    Decode a JWT only when it is explicitly marked as a browser
    session.

    Ordinary API access tokens cannot silently become browser
    sessions.
    """
    payload = decode_access_token(token)

    if payload is None:
        return None

    if payload.get("token_use") != SESSION_TOKEN_USE:
        return None

    user_id = payload.get("user_id")
    role = payload.get("role")
    token_id = payload.get("jti")

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
        or not isinstance(role, str)
        or not role.strip()
        or not isinstance(token_id, str)
        or not token_id.strip()
    ):
        return None

    issued_at = _timestamp_to_datetime(
        payload.get("iat")
    )

    expires_at = _timestamp_to_datetime(
        payload.get("exp")
    )

    if (
        issued_at is None
        or expires_at is None
        or expires_at <= issued_at
    ):
        return None

    try:
        canonical_role = canonical_role_name(
            role
        )
    except CanonicalRoleResolutionError:
        return None

    identity = BrowserSessionIdentity(
        user_id=user_id.strip(),
        role=canonical_role,
        token_id=token_id.strip(),
        issued_at=issued_at,
        expires_at=expires_at,
    )

    if identity.is_expired:
        return None

    return identity


def set_browser_session_cookie(
    response: Response,
    token: str,
    *,
    settings: BrowserSessionSettings | None = None,
) -> BrowserSessionIdentity:
    """
    Attach a validated browser-session token using a hardened
    __Host- cookie.
    """
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_session_settings()
    )

    identity = decode_browser_session_token(
        token
    )

    if identity is None:
        raise ValueError(
            "Cannot set an invalid browser-session token."
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


def clear_browser_session_cookie(
    response: Response,
    *,
    settings: BrowserSessionSettings | None = None,
) -> None:
    """
    Remove the browser-session cookie using the same security
    attributes used when it was created.
    """
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_session_settings()
    )

    response.delete_cookie(
        key=resolved_settings.cookie_name,
        path=resolved_settings.path,
        secure=resolved_settings.secure,
        httponly=resolved_settings.httponly,
        samesite=resolved_settings.samesite,
    )


def get_browser_session_token(
    request: Request,
    *,
    settings: BrowserSessionSettings | None = None,
) -> str | None:
    resolved_settings = (
        settings
        if settings is not None
        else get_browser_session_settings()
    )

    token = request.cookies.get(
        resolved_settings.cookie_name
    )

    if not isinstance(token, str):
        return None

    normalized_token = token.strip()

    return normalized_token or None