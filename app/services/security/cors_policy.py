from __future__ import annotations

import os
from urllib.parse import urlsplit


CORS_ORIGINS_ENV = "CGMS_ALLOWED_ORIGINS"


class CorsPolicyConfigurationError(RuntimeError):
    """
    Raised when the configured CORS origin allowlist contains
    an unsafe or invalid origin.
    """


def _normalize_origin(origin: str) -> str:
    candidate = origin.strip()

    if not candidate:
        raise CorsPolicyConfigurationError(
            "CORS origins must not contain empty entries."
        )

    if candidate == "*":
        raise CorsPolicyConfigurationError(
            "Wildcard CORS origins are not permitted."
        )

    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise CorsPolicyConfigurationError(
            f"Invalid CORS origin: {candidate!r}."
        ) from exc

    scheme = parsed.scheme.lower()

    if scheme not in {"http", "https"}:
        raise CorsPolicyConfigurationError(
            "CORS origins must use http or https."
        )

    if not parsed.netloc or not parsed.hostname:
        raise CorsPolicyConfigurationError(
            f"Invalid CORS origin: {candidate!r}."
        )

    if parsed.username or parsed.password:
        raise CorsPolicyConfigurationError(
            "CORS origins must not contain credentials."
        )

    if parsed.query or parsed.fragment:
        raise CorsPolicyConfigurationError(
            "CORS origins must not contain a query or fragment."
        )

    if parsed.path not in {"", "/"}:
        raise CorsPolicyConfigurationError(
            "CORS origins must not contain a path."
        )

    hostname = parsed.hostname.lower()

    # urlsplit removes IPv6 brackets from hostname, so restore
    # them when constructing the normalized origin.
    if ":" in hostname:
        authority = f"[{hostname}]"
    else:
        authority = hostname

    # Normalize default ports because browser Origin headers
    # ordinarily omit them.
    if (
        scheme == "http"
        and port == 80
    ) or (
        scheme == "https"
        and port == 443
    ):
        port = None

    if port is not None:
        authority = f"{authority}:{port}"

    return f"{scheme}://{authority}"


def parse_allowed_cors_origins(
    raw_value: str | None,
) -> list[str]:
    """
    Parse a comma-separated list of exact browser origins.

    A blank configuration permits no cross-origin browser
    access. Same-origin requests do not require CORS and remain
    available.
    """
    if raw_value is None or not raw_value.strip():
        return []

    normalized_origins: list[str] = []
    seen: set[str] = set()

    for raw_origin in raw_value.split(","):
        normalized_origin = _normalize_origin(
            raw_origin
        )

        if normalized_origin in seen:
            continue

        seen.add(normalized_origin)
        normalized_origins.append(
            normalized_origin
        )

    return normalized_origins


def get_allowed_cors_origins() -> list[str]:
    return parse_allowed_cors_origins(
        os.getenv(CORS_ORIGINS_ENV)
    )