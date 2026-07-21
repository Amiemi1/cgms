from __future__ import annotations

import pytest

from app.services.security.cors_policy import (
    CorsPolicyConfigurationError,
    get_allowed_cors_origins,
    parse_allowed_cors_origins,
)


def test_missing_configuration_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "CGMS_ALLOWED_ORIGINS",
        raising=False,
    )

    assert get_allowed_cors_origins() == []


@pytest.mark.parametrize(
    "raw_value",
    [
        None,
        "",
        " ",
        "   ",
    ],
)
def test_blank_configuration_returns_no_origins(
    raw_value: str | None,
) -> None:
    assert (
        parse_allowed_cors_origins(raw_value)
        == []
    )


def test_parses_multiple_exact_origins() -> None:
    origins = parse_allowed_cors_origins(
        (
            "https://app.example.com,"
            "http://localhost:3000"
        )
    )

    assert origins == [
        "https://app.example.com",
        "http://localhost:3000",
    ]


def test_normalizes_case_and_trailing_slash() -> None:
    origins = parse_allowed_cors_origins(
        " HTTPS://APP.EXAMPLE.COM/ "
    )

    assert origins == [
        "https://app.example.com"
    ]


def test_removes_duplicate_origins() -> None:
    origins = parse_allowed_cors_origins(
        (
            "https://app.example.com,"
            "https://APP.EXAMPLE.COM/,"
            "https://app.example.com"
        )
    )

    assert origins == [
        "https://app.example.com"
    ]


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (
            "https://example.com:443",
            ["https://example.com"],
        ),
        (
            "http://example.com:80",
            ["http://example.com"],
        ),
        (
            "https://example.com:8443",
            ["https://example.com:8443"],
        ),
    ],
)
def test_normalizes_ports(
    raw_value: str,
    expected: list[str],
) -> None:
    assert (
        parse_allowed_cors_origins(raw_value)
        == expected
    )


def test_supports_local_ipv6_origin() -> None:
    assert parse_allowed_cors_origins(
        "http://[::1]:3000"
    ) == [
        "http://[::1]:3000"
    ]


@pytest.mark.parametrize(
    "raw_value",
    [
        "*",
        "https://example.com,*",
        "ftp://example.com",
        "example.com",
        "https://example.com/application",
        "https://example.com?value=1",
        "https://example.com#section",
        "https://user:password@example.com",
        "https://example.com:not-a-port",
        "https://",
    ],
)
def test_unsafe_or_invalid_origins_are_rejected(
    raw_value: str,
) -> None:
    with pytest.raises(
        CorsPolicyConfigurationError
    ):
        parse_allowed_cors_origins(
            raw_value
        )


def test_environment_configuration_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_ALLOWED_ORIGINS",
        (
            "https://portal.example.com,"
            "http://localhost:3000"
        ),
    )

    assert get_allowed_cors_origins() == [
        "https://portal.example.com",
        "http://localhost:3000",
    ]