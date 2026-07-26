from __future__ import annotations

from scripts.operations.production_preflight import (
    render_results,
    run_preflight,
)


def _valid_environment() -> dict[str, str]:
    return {
        "ENVIRONMENT": "production",
        "DATABASE_URL": (
            "postgresql+psycopg://"
            "user:strong-password@"
            "database.internal:5432/cgms"
        ),
        "CGMS_JWT_SECRET": (
            "jwt-secret-with-more-than-32-characters"
        ),
        "CGMS_LOGIN_THROTTLE_SECRET": (
            "throttle-secret-with-more-than-32-characters"
        ),
        "CGMS_SQL_ECHO": "false",
        "CGMS_DATABASE_STARTUP_POLICY": "strict",
        "CGMS_SESSION_COOKIE_NAME": (
            "__Host-cgms_session"
        ),
        "CGMS_CSRF_COOKIE_NAME": (
            "__Host-cgms_csrf"
        ),
        "CGMS_ALLOWED_ORIGINS": (
            "https://portal.example.com"
        ),
        "CGMS_TRUSTED_PROXY_CIDRS": (
            "10.10.0.0/16"
        ),
    }


def _statuses(
    environment: dict[str, str],
) -> dict[str, str]:
    return {
        result.control: result.status
        for result in run_preflight(
            environment
        )
    }


def test_valid_production_environment_has_no_failures(
) -> None:
    results = run_preflight(
        _valid_environment()
    )

    assert all(
        result.status != "FAIL"
        for result in results
    )


def test_development_environment_fails(
) -> None:
    environment = _valid_environment()
    environment["ENVIRONMENT"] = "development"

    assert (
        _statuses(environment)["ENVIRONMENT"]
        == "FAIL"
    )


def test_missing_jwt_secret_fails(
) -> None:
    environment = _valid_environment()
    environment["CGMS_JWT_SECRET"] = ""

    assert (
        _statuses(environment)[
            "CGMS_JWT_SECRET"
        ]
        == "FAIL"
    )


def test_placeholder_jwt_secret_fails(
) -> None:
    environment = _valid_environment()
    environment["CGMS_JWT_SECRET"] = (
        "replace_with_a_random_secret_123456789"
    )

    assert (
        _statuses(environment)[
            "CGMS_JWT_SECRET"
        ]
        == "FAIL"
    )


def test_missing_dedicated_throttle_secret_warns(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_LOGIN_THROTTLE_SECRET"
    ] = ""

    assert (
        _statuses(environment)[
            "CGMS_LOGIN_THROTTLE_SECRET"
        ]
        == "WARN"
    )


def test_sql_echo_enabled_fails(
) -> None:
    environment = _valid_environment()
    environment["CGMS_SQL_ECHO"] = "true"

    assert (
        _statuses(environment)[
            "CGMS_SQL_ECHO"
        ]
        == "FAIL"
    )


def test_warning_database_policy_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_DATABASE_STARTUP_POLICY"
    ] = "warn"

    assert (
        _statuses(environment)[
            "CGMS_DATABASE_STARTUP_POLICY"
        ]
        == "FAIL"
    )


def test_non_host_cookie_name_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_SESSION_COOKIE_NAME"
    ] = "cgms_session"

    assert (
        _statuses(environment)[
            "CGMS_SESSION_COOKIE_NAME"
        ]
        == "FAIL"
    )


def test_http_cors_origin_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_ALLOWED_ORIGINS"
    ] = "http://portal.example.com"

    assert (
        _statuses(environment)[
            "CGMS_ALLOWED_ORIGINS"
        ]
        == "FAIL"
    )


def test_wildcard_cors_origin_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_ALLOWED_ORIGINS"
    ] = "*"

    assert (
        _statuses(environment)[
            "CGMS_ALLOWED_ORIGINS"
        ]
        == "FAIL"
    )


def test_invalid_proxy_cidr_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_TRUSTED_PROXY_CIDRS"
    ] = "not-a-network"

    assert (
        _statuses(environment)[
            "CGMS_TRUSTED_PROXY_CIDRS"
        ]
        == "FAIL"
    )


def test_invalid_throttle_limit_fails(
) -> None:
    environment = _valid_environment()
    environment[
        "CGMS_LOGIN_THROTTLE_PAIR_LIMIT"
    ] = "1"

    assert (
        _statuses(environment)[
            "CGMS_LOGIN_THROTTLE_PAIR_LIMIT"
        ]
        == "FAIL"
    )


def test_rendered_output_never_contains_values(
) -> None:
    environment = _valid_environment()
    results = run_preflight(environment)

    rendered = render_results(results)

    assert environment[
        "CGMS_JWT_SECRET"
    ] not in rendered

    assert environment[
        "DATABASE_URL"
    ] not in rendered

    assert environment[
        "CGMS_ALLOWED_ORIGINS"
    ] not in rendered

    assert (
        "No environment values are displayed."
        in rendered
    )
