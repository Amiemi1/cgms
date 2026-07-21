from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt


ALGORITHM = "HS256"
DEFAULT_TOKEN_EXPIRE_MINUTES = 60 * 24
DEFAULT_ISSUER = "cgms"
DEFAULT_AUDIENCE = "cgms-dashboard"


class JWTConfigurationError(RuntimeError):
    """
    Raised when secure JWT configuration is unavailable.
    """


def _get_secret_key() -> str:
    secret_key = os.getenv(
        "CGMS_JWT_SECRET",
        "",
    ).strip()

    if len(secret_key) < 32:
        raise JWTConfigurationError(
            "CGMS_JWT_SECRET must be configured with at "
            "least 32 characters."
        )

    return secret_key


def _get_token_expiry_minutes() -> int:
    raw_value = os.getenv(
        "CGMS_JWT_EXPIRE_MINUTES",
        str(DEFAULT_TOKEN_EXPIRE_MINUTES),
    )

    try:
        minutes = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise JWTConfigurationError(
            "CGMS_JWT_EXPIRE_MINUTES must be an integer."
        ) from exc

    if minutes <= 0:
        raise JWTConfigurationError(
            "CGMS_JWT_EXPIRE_MINUTES must be greater than zero."
        )

    return minutes


def _get_issuer() -> str:
    return (
        os.getenv(
            "CGMS_JWT_ISSUER",
            DEFAULT_ISSUER,
        ).strip()
        or DEFAULT_ISSUER
    )


def _get_audience() -> str:
    return (
        os.getenv(
            "CGMS_JWT_AUDIENCE",
            DEFAULT_AUDIENCE,
        ).strip()
        or DEFAULT_AUDIENCE
    )


def create_access_token(
    data: dict[str, Any],
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed CGMS access token.

    The token always receives controlled expiration, issuer,
    audience, issued-at, not-before and token-ID claims.
    """
    payload = data.copy()

    user_id = payload.get(
        "sub",
        payload.get("user_id"),
    )

    if user_id is None or not str(user_id).strip():
        raise ValueError(
            "Access-token data must include user_id or sub."
        )

    now = datetime.now(timezone.utc)

    expiration = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=_get_token_expiry_minutes()
        )
    )

    normalized_user_id = str(user_id).strip()

    role = str(
        payload.get("role", "viewer")
    ).strip().lower()

    payload.update(
        {
            "sub": normalized_user_id,
            "user_id": normalized_user_id,
            "role": role,
            "iat": now,
            "nbf": now,
            "exp": expiration,
            "iss": _get_issuer(),
            "aud": _get_audience(),
            "jti": str(uuid4()),
        }
    )

    return jwt.encode(
        payload,
        _get_secret_key(),
        algorithm=ALGORITHM,
    )


def decode_access_token(
    token: str,
) -> dict[str, Any] | None:
    """
    Validate and decode a CGMS access token.

    Invalid, expired, improperly issued or incorrectly
    configured tokens fail closed and return None.
    """
    if not token or not token.strip():
        return None

    try:
        payload = jwt.decode(
            token.strip(),
            _get_secret_key(),
            algorithms=[ALGORITHM],
            audience=_get_audience(),
            issuer=_get_issuer(),
            options={
                "require": [
                    "sub",
                    "iat",
                    "nbf",
                    "exp",
                    "iss",
                    "aud",
                    "jti",
                ]
            },
        )
    except (
        jwt.InvalidTokenError,
        JWTConfigurationError,
        TypeError,
        ValueError,
    ):
        return None

    user_id = payload.get("sub")
    role = payload.get("role")

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
    ):
        return None

    if (
        not isinstance(role, str)
        or not role.strip()
    ):
        return None

    payload["user_id"] = user_id.strip()
    payload["role"] = role.strip().lower()

    return payload