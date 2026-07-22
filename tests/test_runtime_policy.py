from __future__ import annotations

import logging

import pytest

from app.core.runtime_policy import (
    DatabaseStartupError,
    RuntimePolicyConfigurationError,
    get_database_startup_policy,
    get_runtime_environment,
    get_sql_echo_enabled,
    initialize_database_schema,
)


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        ("development", "development"),
        ("dev", "development"),
        ("test", "test"),
        ("testing", "test"),
        ("staging", "staging"),
        ("stage", "staging"),
        ("production", "production"),
        ("prod", "production"),
    ],
)
def test_runtime_environment_aliases(
    supplied: str,
    expected: str,
) -> None:
    assert (
        get_runtime_environment(supplied)
        == expected
    )


def test_unknown_runtime_environment_fails_closed(
) -> None:
    with pytest.raises(
        RuntimePolicyConfigurationError,
    ):
        get_runtime_environment(
            "prdduction"
        )


def test_sql_echo_defaults_disabled(
) -> None:
    assert (
        get_sql_echo_enabled(
            environment="development"
        )
        is False
    )


@pytest.mark.parametrize(
    "supplied",
    [
        "1",
        "true",
        "yes",
        "on",
    ],
)
def test_sql_echo_can_be_enabled_in_development(
    supplied: str,
) -> None:
    assert (
        get_sql_echo_enabled(
            supplied,
            environment="development",
        )
        is True
    )


@pytest.mark.parametrize(
    "environment",
    [
        "staging",
        "production",
    ],
)
def test_sql_echo_is_rejected_in_production_like_environments(
    environment: str,
) -> None:
    with pytest.raises(
        RuntimePolicyConfigurationError,
    ):
        get_sql_echo_enabled(
            "true",
            environment=environment,
        )


def test_invalid_sql_echo_value_is_rejected(
) -> None:
    with pytest.raises(
        RuntimePolicyConfigurationError,
    ):
        get_sql_echo_enabled(
            "verbose",
            environment="development",
        )


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ("development", "warn"),
        ("test", "warn"),
        ("staging", "strict"),
        ("production", "strict"),
    ],
)
def test_database_startup_policy_defaults(
    environment: str,
    expected: str,
) -> None:
    assert (
        get_database_startup_policy(
            environment=environment
        )
        == expected
    )


@pytest.mark.parametrize(
    "environment",
    [
        "staging",
        "production",
    ],
)
def test_production_like_database_policy_cannot_be_downgraded(
    environment: str,
) -> None:
    with pytest.raises(
        RuntimePolicyConfigurationError,
    ):
        get_database_startup_policy(
            "warn",
            environment=environment,
        )


def test_development_database_failure_warns_and_returns_false(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_create_all(
        engine: object,
    ) -> None:
        raise RuntimeError(
            "database unavailable"
        )

    with caplog.at_level(
        logging.ERROR
    ):
        result = initialize_database_schema(
            create_all=fail_create_all,
            engine=object(),
            environment="development",
            startup_policy="warn",
        )

    assert result is False

    assert (
        "database_schema_initialization_warning"
        in caplog.text
    )


def test_production_database_failure_fails_fast(
) -> None:
    cause = RuntimeError(
        "database unavailable"
    )

    def fail_create_all(
        engine: object,
    ) -> None:
        raise cause

    with pytest.raises(
        DatabaseStartupError,
    ) as exception_info:
        initialize_database_schema(
            create_all=fail_create_all,
            engine=object(),
            environment="production",
        )

    assert (
        exception_info.value.__cause__
        is cause
    )


def test_database_schema_success_returns_true(
) -> None:
    calls: list[object] = []
    engine = object()

    def create_all(
        supplied_engine: object,
    ) -> None:
        calls.append(
            supplied_engine
        )

    result = initialize_database_schema(
        create_all=create_all,
        engine=engine,
        environment="production",
    )

    assert result is True
    assert calls == [engine]
