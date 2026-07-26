from __future__ import annotations

import ipaddress
import os
import re
import sys
from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit


_ALLOWED_ENVIRONMENTS = {
    "staging",
    "production",
}

_TRUE_VALUES = {
    "1",
    "true",
    "yes",
    "on",
}

_FALSE_VALUES = {
    "0",
    "false",
    "no",
    "off",
    "",
}

_PLACEHOLDER_MARKERS = {
    "replace_with",
    "changeme",
    "change_me",
    "example",
    "your_",
}

_COOKIE_NAME_PATTERN = re.compile(
    r"^__Host-[A-Za-z0-9._-]+$"
)


@dataclass(frozen=True, slots=True)
class CheckResult:
    control: str
    status: str
    message: str


def _result(
    control: str,
    status: str,
    message: str,
) -> CheckResult:
    return CheckResult(
        control=control,
        status=status,
        message=message,
    )


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().casefold()

    return any(
        marker in normalized
        for marker in _PLACEHOLDER_MARKERS
    )


def _read_integer(
    environment: Mapping[str, str],
    variable_name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> CheckResult:
    raw_value = environment.get(
        variable_name,
        str(default),
    ).strip()

    try:
        value = int(raw_value)
    except ValueError:
        return _result(
            variable_name,
            "FAIL",
            "must be an integer",
        )

    if not minimum <= value <= maximum:
        return _result(
            variable_name,
            "FAIL",
            (
                f"must be between {minimum} "
                f"and {maximum}"
            ),
        )

    return _result(
        variable_name,
        "PASS",
        "is within the supported range",
    )


def _check_environment(
    environment: Mapping[str, str],
) -> CheckResult:
    value = environment.get(
        "ENVIRONMENT",
        "",
    ).strip().casefold()

    if value not in _ALLOWED_ENVIRONMENTS:
        return _result(
            "ENVIRONMENT",
            "FAIL",
            "must be staging or production",
        )

    return _result(
        "ENVIRONMENT",
        "PASS",
        "uses a production-like runtime policy",
    )


def _check_database_url(
    environment: Mapping[str, str],
) -> list[CheckResult]:
    value = environment.get(
        "DATABASE_URL",
        "",
    ).strip()

    if not value:
        return [
            _result(
                "DATABASE_URL",
                "FAIL",
                "is required",
            )
        ]

    lowered = value.casefold()

    if (
        not lowered.startswith(
            (
                "postgresql://",
                "postgresql+psycopg://",
            )
        )
        or _is_placeholder(value)
    ):
        return [
            _result(
                "DATABASE_URL",
                "FAIL",
                "must be a non-placeholder PostgreSQL URL",
            )
        ]

    results = [
        _result(
            "DATABASE_URL",
            "PASS",
            "is configured without displaying its value",
        )
    ]

    if (
        "localhost" in lowered
        or "127.0.0.1" in lowered
        or "@db:" in lowered
        or "postgres:postgres" in lowered
        or "cgms_password" in lowered
    ):
        results.append(
            _result(
                "DATABASE_URL topology",
                "WARN",
                (
                    "resembles a local-development database; "
                    "confirm the target topology and credentials"
                ),
            )
        )

    return results


def _check_secret(
    environment: Mapping[str, str],
    variable_name: str,
    *,
    required: bool,
) -> CheckResult:
    value = environment.get(
        variable_name,
        "",
    ).strip()

    if not value:
        if required:
            return _result(
                variable_name,
                "FAIL",
                "is required",
            )

        return _result(
            variable_name,
            "WARN",
            (
                "is not configured; the documented "
                "JWT-secret fallback will be used"
            ),
        )

    if len(value) < 32 or _is_placeholder(value):
        return _result(
            variable_name,
            "FAIL",
            (
                "must be a non-placeholder secret "
                "of at least 32 characters"
            ),
        )

    return _result(
        variable_name,
        "PASS",
        "meets the minimum secret policy",
    )


def _check_sql_echo(
    environment: Mapping[str, str],
) -> CheckResult:
    value = environment.get(
        "CGMS_SQL_ECHO",
        "",
    ).strip().casefold()

    if value in _FALSE_VALUES:
        return _result(
            "CGMS_SQL_ECHO",
            "PASS",
            "is disabled",
        )

    if value in _TRUE_VALUES:
        return _result(
            "CGMS_SQL_ECHO",
            "FAIL",
            "cannot be enabled in staging or production",
        )

    return _result(
        "CGMS_SQL_ECHO",
        "FAIL",
        "must be a recognized boolean value",
    )


def _check_database_policy(
    environment: Mapping[str, str],
) -> CheckResult:
    value = environment.get(
        "CGMS_DATABASE_STARTUP_POLICY",
        "strict",
    ).strip().casefold()

    if value != "strict":
        return _result(
            "CGMS_DATABASE_STARTUP_POLICY",
            "FAIL",
            "must be strict in staging or production",
        )

    return _result(
        "CGMS_DATABASE_STARTUP_POLICY",
        "PASS",
        "is fail-fast",
    )


def _check_cookie_name(
    environment: Mapping[str, str],
    variable_name: str,
    default: str,
) -> CheckResult:
    value = environment.get(
        variable_name,
        default,
    ).strip()

    if _COOKIE_NAME_PATTERN.fullmatch(
        value
    ) is None:
        return _result(
            variable_name,
            "FAIL",
            (
                "must use the __Host- prefix and "
                "the supported character set"
            ),
        )

    return _result(
        variable_name,
        "PASS",
        "uses a host-bound cookie name",
    )


def _check_cors(
    environment: Mapping[str, str],
) -> list[CheckResult]:
    raw_value = environment.get(
        "CGMS_ALLOWED_ORIGINS",
        "",
    ).strip()

    if not raw_value:
        return [
            _result(
                "CGMS_ALLOWED_ORIGINS",
                "PASS",
                "is blank for same-origin access",
            )
        ]

    candidates = raw_value.split(",")

    if any(
        not candidate.strip()
        for candidate in candidates
    ):
        return [
            _result(
                "CGMS_ALLOWED_ORIGINS",
                "FAIL",
                "contains an empty origin entry",
            )
        ]

    for candidate in candidates:
        origin = candidate.strip()

        if "*" in origin:
            return [
                _result(
                    "CGMS_ALLOWED_ORIGINS",
                    "FAIL",
                    "must not contain a wildcard",
                )
            ]

        parsed = urlsplit(origin)

        if (
            parsed.scheme.casefold() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            return [
                _result(
                    "CGMS_ALLOWED_ORIGINS",
                    "FAIL",
                    (
                        "must contain exact HTTPS origins "
                        "without credentials, paths, queries "
                        "or fragments"
                    ),
                )
            ]

        if parsed.path == "/" and origin.endswith("/"):
            return [
                _result(
                    "CGMS_ALLOWED_ORIGINS",
                    "FAIL",
                    "origins must not include a trailing path",
                )
            ]

        if parsed.hostname.casefold() in {
            "localhost",
            "127.0.0.1",
            "::1",
        }:
            return [
                _result(
                    "CGMS_ALLOWED_ORIGINS",
                    "FAIL",
                    "must not contain a loopback production origin",
                )
            ]

    return [
        _result(
            "CGMS_ALLOWED_ORIGINS",
            "PASS",
            "contains exact HTTPS origins only",
        )
    ]


def _check_trusted_proxies(
    environment: Mapping[str, str],
) -> CheckResult:
    raw_value = environment.get(
        "CGMS_TRUSTED_PROXY_CIDRS",
        "",
    ).strip()

    if not raw_value:
        return _result(
            "CGMS_TRUSTED_PROXY_CIDRS",
            "WARN",
            (
                "is blank; confirm that CGMS is not expected "
                "to trust proxy forwarding headers"
            ),
        )

    for candidate in raw_value.split(","):
        normalized = candidate.strip()

        if not normalized:
            continue

        try:
            ipaddress.ip_network(
                normalized,
                strict=False,
            )
        except ValueError:
            return _result(
                "CGMS_TRUSTED_PROXY_CIDRS",
                "FAIL",
                "contains an invalid CIDR network",
            )

    return _result(
        "CGMS_TRUSTED_PROXY_CIDRS",
        "PASS",
        "contains syntactically valid CIDR networks",
    )


def run_preflight(
    environment: Mapping[str, str],
) -> list[CheckResult]:
    results: list[CheckResult] = [
        _check_environment(environment),
        *_check_database_url(environment),
        _check_secret(
            environment,
            "CGMS_JWT_SECRET",
            required=True,
        ),
        _check_secret(
            environment,
            "CGMS_LOGIN_THROTTLE_SECRET",
            required=False,
        ),
        _check_sql_echo(environment),
        _check_database_policy(environment),
        _check_cookie_name(
            environment,
            "CGMS_SESSION_COOKIE_NAME",
            "__Host-cgms_session",
        ),
        _check_cookie_name(
            environment,
            "CGMS_CSRF_COOKIE_NAME",
            "__Host-cgms_csrf",
        ),
        _read_integer(
            environment,
            "CGMS_JWT_EXPIRE_MINUTES",
            default=1440,
            minimum=1,
            maximum=10080,
        ),
        _read_integer(
            environment,
            "CGMS_SESSION_EXPIRE_MINUTES",
            default=30,
            minimum=5,
            maximum=1440,
        ),
        _read_integer(
            environment,
            "CGMS_CSRF_EXPIRE_SECONDS",
            default=600,
            minimum=120,
            maximum=3600,
        ),
        _read_integer(
            environment,
            "CGMS_LOGIN_THROTTLE_WINDOW_SECONDS",
            default=900,
            minimum=60,
            maximum=86400,
        ),
        _read_integer(
            environment,
            "CGMS_LOGIN_THROTTLE_PAIR_LIMIT",
            default=5,
            minimum=2,
            maximum=100,
        ),
        _read_integer(
            environment,
            "CGMS_LOGIN_THROTTLE_NETWORK_LIMIT",
            default=25,
            minimum=5,
            maximum=1000,
        ),
        _read_integer(
            environment,
            "CGMS_LOGIN_THROTTLE_BLOCK_SECONDS",
            default=900,
            minimum=60,
            maximum=86400,
        ),
        _read_integer(
            environment,
            "CGMS_LOGIN_THROTTLE_RETENTION_DAYS",
            default=7,
            minimum=1,
            maximum=90,
        ),
        *_check_cors(environment),
        _check_trusted_proxies(environment),
    ]

    return results


def render_results(
    results: list[CheckResult],
) -> str:
    lines = [
        "CGMS production preflight",
        "No environment values are displayed.",
        "",
    ]

    for result in results:
        lines.append(
            f"{result.status:4} "
            f"{result.control}: "
            f"{result.message}"
        )

    failures = sum(
        result.status == "FAIL"
        for result in results
    )

    warnings = sum(
        result.status == "WARN"
        for result in results
    )

    lines.extend(
        [
            "",
            (
                "Summary: "
                f"{failures} failure(s), "
                f"{warnings} warning(s)"
            ),
        ]
    )

    return "\n".join(lines)


def main() -> int:
    results = run_preflight(os.environ)

    print(
        render_results(results)
    )

    return (
        1
        if any(
            result.status == "FAIL"
            for result in results
        )
        else 0
    )


if __name__ == "__main__":
    sys.exit(main())
