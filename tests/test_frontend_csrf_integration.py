from __future__ import annotations

import re
from collections import Counter
from pathlib import Path


DASHBOARD_PATH = Path(
    "app/dashboard/templates/dashboard.html"
)

OPERATOR_PATH = Path(
    "app/dashboard/templates/operator_console.html"
)

PRODUCT_READINESS_PATH = Path(
    "app/dashboard/templates/"
    "product_readiness_dashboard.html"
)

HELPER_NAME = "cgmsAuthenticatedFetch"

UNSAFE_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}

EXPECTED_DASHBOARD_UNSAFE = Counter(
    {
        ("POST", "/runtime/event"): 1,
        (
            "PATCH",
            "/dashboard/memory/${id}/complete",
        ): 2,
        (
            "DELETE",
            "/dashboard/memory/${id}",
        ): 1,
        (
            "PATCH",
            "/dashboard/memory/${id}/reopen",
        ): 1,
        (
            "PATCH",
            "/dashboard/memory/${id}/restore",
        ): 1,
        (
            "DELETE",
            (
                "/dashboard/memory/"
                "deduplicate/${userId}"
            ),
        ): 1,
        (
            "POST",
            "/dashboard/tasks/breakdown",
        ): 2,
        (
            "PATCH",
            (
                "/dashboard/memory/"
                "${memoryId}/goal/${goalId}"
            ),
        ): 1,
        (
            "POST",
            (
                "/dashboard/memory/"
                "${taskId}/complete"
            ),
        ): 1,
        (
            "POST",
            "/dashboard/tasks/${id}/complete",
        ): 1,
        (
            "POST",
            "/dashboard/tasks/${userId}",
        ): 1,
    }
)

EXPECTED_OPERATOR_UNSAFE = Counter(
    {
        (
            "POST",
            "/operator/action",
        ): 1,
    }
)


def extract_balanced_call(
    source: str,
    call_start: int,
) -> tuple[str, int]:
    opening_parenthesis = source.find(
        "(",
        call_start,
    )

    if opening_parenthesis < 0:
        raise AssertionError(
            "Call opening parenthesis is unavailable."
        )

    depth = 0
    index = opening_parenthesis

    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False

    while index < len(source):
        character = source[index]

        next_character = (
            source[index + 1]
            if index + 1 < len(source)
            else ""
        )

        if line_comment:
            if character == "\n":
                line_comment = False

            index += 1
            continue

        if block_comment:
            if (
                character == "*"
                and next_character == "/"
            ):
                block_comment = False
                index += 2
                continue

            index += 1
            continue

        if quote is not None:
            if escaped:
                escaped = False
                index += 1
                continue

            if character == "\\":
                escaped = True
                index += 1
                continue

            if character == quote:
                quote = None

            index += 1
            continue

        if (
            character == "/"
            and next_character == "/"
        ):
            line_comment = True
            index += 2
            continue

        if (
            character == "/"
            and next_character == "*"
        ):
            block_comment = True
            index += 2
            continue

        if character in {
            "'",
            '"',
            "`",
        }:
            quote = character
            index += 1
            continue

        if character == "(":
            depth += 1

        elif character == ")":
            depth -= 1

            if depth == 0:
                return (
                    source[
                        call_start:
                        index + 1
                    ],
                    index + 1,
                )

        index += 1

    raise AssertionError(
        "Unterminated JavaScript call."
    )


def resolve_method(
    call_source: str,
) -> str:
    match = re.search(
        r"""
        \bmethod\s*:\s*
        ["']
        (?P<method>
            GET
            |
            POST
            |
            PUT
            |
            PATCH
            |
            DELETE
        )
        ["']
        """,
        call_source,
        flags=(
            re.IGNORECASE
            | re.VERBOSE
        ),
    )

    if match is None:
        return "GET"

    return match.group(
        "method"
    ).upper()


def resolve_endpoint(
    call_source: str,
) -> str | None:
    match = re.search(
        r"""
        \(
            \s*
            (?P<quote>
                `
                |
                "
                |
                '
            )
            (?P<endpoint>
                .*?
            )
            (?P=quote)
        """,
        call_source,
        flags=(
            re.DOTALL
            | re.VERBOSE
        ),
    )

    if match is None:
        return None

    endpoint = (
        match.group(
            "endpoint"
        )
        .strip()
        .replace(
            "\n",
            " ",
        )
    )

    return endpoint


def request_records(
    path: Path,
) -> list[
    tuple[str, str, str]
]:
    source = path.read_text(
        encoding="utf-8",
        errors="strict",
    )

    pattern = re.compile(
        r"""
        \b
        (?P<name>
            cgmsAuthenticatedFetch
            |
            fetch
        )
        \s*\(
        """,
        flags=re.VERBOSE,
    )

    records: list[
        tuple[str, str, str]
    ] = []

    for match in pattern.finditer(
        source
    ):
        call_source, _ = (
            extract_balanced_call(
                source,
                match.start(),
            )
        )

        endpoint = resolve_endpoint(
            call_source
        )

        if (
            endpoint is None
            or not endpoint.startswith("/")
        ):
            continue

        records.append(
            (
                match.group("name"),
                resolve_method(
                    call_source
                ),
                endpoint,
            )
        )

    return records


def unsafe_application_records(
    path: Path,
) -> list[
    tuple[str, str, str]
]:
    return [
        record
        for record in request_records(
            path
        )
        if (
            record[1]
            in UNSAFE_METHODS
        )
    ]


def test_dashboard_unsafe_requests_use_authenticated_fetch(
) -> None:
    records = unsafe_application_records(
        DASHBOARD_PATH
    )

    assert len(records) == 13

    assert all(
        name == HELPER_NAME
        for name, _, _ in records
    )

    assert Counter(
        (
            method,
            endpoint,
        )
        for _, method, endpoint
        in records
    ) == EXPECTED_DASHBOARD_UNSAFE


def test_operator_mutation_uses_authenticated_fetch(
) -> None:
    records = unsafe_application_records(
        OPERATOR_PATH
    )

    assert records == [
        (
            HELPER_NAME,
            "POST",
            "/operator/action",
        )
    ]

    assert Counter(
        (
            method,
            endpoint,
        )
        for _, method, endpoint
        in records
    ) == EXPECTED_OPERATOR_UNSAFE


def test_templates_contain_complete_csrf_helper_contract(
) -> None:
    for path in (
        DASHBOARD_PATH,
        OPERATOR_PATH,
    ):
        source = path.read_text(
            encoding="utf-8",
            errors="strict",
        )

        assert source.count(
            "// AAE-001 AUTHENTICATED FETCH"
        ) == 1

        assert source.count(
            "async function "
            "cgmsAuthenticatedFetch"
        ) == 1

        assert source.count(
            "async function "
            "cgmsObtainCsrfToken"
        ) == 1

        assert (
            '"/auth/csrf"'
            in source
        )

        assert (
            '"X-CSRF-Token"'
            in source
        )

        assert (
            'credentials: "same-origin"'
            in source
        )

        assert (
            'cache: "no-store"'
            in source
        )

        assert (
            "response.clone().json()"
            in source
        )

        assert (
            "await executeRequest(true)"
            in source
        )

        assert (
            "The authenticated browser request "
            "could not be validated."
            in source
        )


def test_no_raw_unsafe_application_fetch_remains(
) -> None:
    for path in (
        DASHBOARD_PATH,
        OPERATOR_PATH,
    ):
        raw_unsafe = [
            record
            for record
            in unsafe_application_records(
                path
            )
            if record[0] == "fetch"
        ]

        assert raw_unsafe == []


def test_product_readiness_template_remains_read_only(
) -> None:
    source = (
        PRODUCT_READINESS_PATH.read_text(
            encoding="utf-8",
            errors="strict",
        )
    )

    assert (
        "// AAE-001 AUTHENTICATED FETCH"
        not in source
    )

    assert (
        "cgmsAuthenticatedFetch"
        not in source
    )

    assert unsafe_application_records(
        PRODUCT_READINESS_PATH
    ) == []
