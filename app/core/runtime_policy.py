from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any, Literal


DEFAULT_RUNTIME_ENVIRONMENT = "development"

_RUNTIME_ENVIRONMENT_ALIASES = {
    "dev": "development",
    "development": "development",
    "test": "test",
    "testing": "test",
    "stage": "staging",
    "staging": "staging",
    "prod": "production",
    "production": "production",
}

_PRODUCTION_LIKE_ENVIRONMENTS = frozenset({
    "staging",
    "production",
})

_TRUE_VALUES = frozenset({
    "1",
    "true",
    "yes",
    "on",
})

_FALSE_VALUES = frozenset({
    "0",
    "false",
    "no",
    "off",
})

DatabaseStartupPolicy = Literal[
    "strict",
    "warn",
]


class RuntimePolicyConfigurationError(
    RuntimeError
):
    """
    Raised when runtime hardening configuration is invalid or
    would weaken a production-like environment.
    """


class DatabaseStartupError(
    RuntimeError
):
    """
    Raised when database schema initialisation fails under a
    strict startup policy.
    """


def get_runtime_environment(
    raw_value: str | None = None,
) -> str:
    """
    Resolve the canonical CGMS runtime environment.

    Unknown environment names fail closed so a misspelled
    production setting cannot silently inherit development
    behaviour.
    """
    supplied_value = (
        raw_value
        if raw_value is not None
        else os.getenv(
            "ENVIRONMENT",
            DEFAULT_RUNTIME_ENVIRONMENT,
        )
    )

    normalized = supplied_value.strip().lower()

    if not normalized:
        normalized = DEFAULT_RUNTIME_ENVIRONMENT

    environment = (
        _RUNTIME_ENVIRONMENT_ALIASES.get(
            normalized
        )
    )

    if environment is None:
        raise RuntimePolicyConfigurationError(
            "ENVIRONMENT must be one of: "
            "development, test, staging or production."
        )

    return environment


def is_production_like_environment(
    environment: str | None = None,
) -> bool:
    return (
        get_runtime_environment(environment)
        in _PRODUCTION_LIKE_ENVIRONMENTS
    )


def _parse_boolean(
    *,
    variable_name: str,
    raw_value: str | None,
    default: bool,
) -> bool:
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized in _TRUE_VALUES:
        return True

    if normalized in _FALSE_VALUES:
        return False

    raise RuntimePolicyConfigurationError(
        f"{variable_name} must be a boolean value."
    )


def get_sql_echo_enabled(
    raw_value: str | None = None,
    *,
    environment: str | None = None,
) -> bool:
    """
    Resolve SQLAlchemy statement logging.

    SQL echo is disabled by default and cannot be enabled in
    staging or production because it may expose bound parameter
    values in operational logs.
    """
    resolved_environment = (
        get_runtime_environment(environment)
    )

    configured_value = (
        raw_value
        if raw_value is not None
        else os.getenv("CGMS_SQL_ECHO")
    )

    enabled = _parse_boolean(
        variable_name="CGMS_SQL_ECHO",
        raw_value=configured_value,
        default=False,
    )

    if (
        enabled
        and resolved_environment
        in _PRODUCTION_LIKE_ENVIRONMENTS
    ):
        raise RuntimePolicyConfigurationError(
            "CGMS_SQL_ECHO cannot be enabled in "
            "staging or production."
        )

    return enabled


def get_database_startup_policy(
    raw_value: str | None = None,
    *,
    environment: str | None = None,
) -> DatabaseStartupPolicy:
    """
    Resolve the database schema startup policy.

    Staging and production default to strict fail-fast startup.
    Development and test default to warning-only startup so
    isolated workflows can continue when explicitly operating
    without the database.
    """
    resolved_environment = (
        get_runtime_environment(environment)
    )

    configured_value = (
        raw_value
        if raw_value is not None
        else os.getenv(
            "CGMS_DATABASE_STARTUP_POLICY"
        )
    )

    if configured_value is None:
        policy: DatabaseStartupPolicy = (
            "strict"
            if resolved_environment
            in _PRODUCTION_LIKE_ENVIRONMENTS
            else "warn"
        )
    else:
        normalized = (
            configured_value.strip().lower()
        )

        if normalized not in {
            "strict",
            "warn",
        }:
            raise RuntimePolicyConfigurationError(
                "CGMS_DATABASE_STARTUP_POLICY must "
                "be either strict or warn."
            )

        policy = normalized  # type: ignore[assignment]

    if (
        resolved_environment
        in _PRODUCTION_LIKE_ENVIRONMENTS
        and policy != "strict"
    ):
        raise RuntimePolicyConfigurationError(
            "Database startup must use strict policy "
            "in staging and production."
        )

    return policy


def initialize_database_schema(
    *,
    create_all: Callable[[Any], None],
    engine: Any,
    environment: str | None = None,
    startup_policy: str | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    """
    Initialise the SQLModel schema under the resolved runtime
    policy.

    Returns True on success. Under warning-only development/test
    policy, returns False after logging the failure. Under strict
    staging/production policy, raises DatabaseStartupError and
    prevents application startup.
    """
    resolved_environment = (
        get_runtime_environment(environment)
    )

    resolved_policy = (
        get_database_startup_policy(
            startup_policy,
            environment=resolved_environment,
        )
    )

    resolved_logger = (
        logger
        if logger is not None
        else logging.getLogger(
            "cgms.runtime.startup"
        )
    )

    try:
        create_all(engine)

    except Exception as exc:
        if resolved_policy == "strict":
            resolved_logger.exception(
                "database_schema_initialization_failed "
                "environment=%s policy=%s",
                resolved_environment,
                resolved_policy,
            )

            raise DatabaseStartupError(
                "Database schema initialisation failed."
            ) from exc

        resolved_logger.exception(
            "database_schema_initialization_warning "
            "environment=%s policy=%s "
            "continuing_without_database=true",
            resolved_environment,
            resolved_policy,
        )

        return False

    resolved_logger.info(
        "database_schema_initialized "
        "environment=%s policy=%s",
        resolved_environment,
        resolved_policy,
    )

    return True
