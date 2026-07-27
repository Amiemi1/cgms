from __future__ import annotations

import re
from pathlib import Path


REPORT_PATH = Path(
    "docs/product/"
    "CGMS_Commercial_Readiness_Gap_Assessment.md"
)


def report_source() -> str:
    return REPORT_PATH.read_text(
        encoding="utf-8",
        errors="strict",
    )


def readiness_rows(
    source: str,
) -> list[tuple[str, ...]]:
    register = re.search(
        (
            r"## 5\. Consolidated P0/P1 Readiness Register"
            r"(?P<body>.*?)"
            r"## 6\. Capability Findings"
        ),
        source,
        flags=re.DOTALL,
    )

    assert register is not None

    return re.findall(
        (
            r"^\| "
            r"(CAP-\d{3}) "
            r"\| ([^|]+) "
            r"\| (P[01]) "
            r"\| ([^|]+) "
            r"\| ([^|]+) "
            r"\| "
            r"(Validated|Partial|Not Ready|Not Implemented) "
            r"\| (Low|High|Critical) "
            r"\| (Yes|No) \|$"
        ),
        register.group("body"),
        flags=re.MULTILINE,
    )


def test_crg001_report_contains_complete_readiness_register() -> None:
    source = report_source()
    rows = readiness_rows(source)

    assert len(rows) == 20

    assert len(
        {
            row[0]
            for row in rows
        }
    ) == 20

    assert sum(
        row[5] == "Validated"
        for row in rows
    ) == 1

    assert sum(
        row[5] == "Partial"
        for row in rows
    ) == 15

    assert sum(
        row[5] == "Not Ready"
        for row in rows
    ) == 3

    assert sum(
        row[5] == "Not Implemented"
        for row in rows
    ) == 1


def test_crg001_report_records_blockers_and_verdict() -> None:
    source = report_source()
    rows = readiness_rows(source)

    blockers = [
        row[0]
        for row in rows
        if row[7] == "Yes"
    ]

    assert blockers == [
        "CAP-002",
        "CAP-003",
        "CAP-004",
        "CAP-005",
        "CAP-015",
        "CAP-016",
        "CAP-017",
        "CAP-018",
        "CAP-019",
        "CAP-021",
    ]

    assert (
        "CRG-001 pilot readiness verdict: NOT READY"
        in source
    )

    assert (
        "P0 commercial blockers | 4"
        in source
    )

    assert (
        "Total commercial blockers | 10"
        in source
    )


def test_crg001_report_preserves_governance_boundary() -> None:
    source = report_source()

    remediation_stages = re.findall(
        r"^\| (\d{1,2}) \| ",
        source,
        flags=re.MULTILINE,
    )

    assert remediation_stages == [
        str(value)
        for value in range(1, 11)
    ]

    assert (
        "CRG-001 remains an assessment "
        "and governance-closure milestone."
        in source
    )

    assert (
        "This document does not authorize:"
        in source
    )

    assert (
        "Each remediation milestone requires "
        "an applicable EG-001 classification"
        in source
    )

    assert (
        "focused CRG-001 closure validation: "
        "**12 passed**"
        in source
    )

    assert (
        "complete final-state regression validation: "
        "**540 passed** with **37 known "
        "deprecation warnings**"
        in source
    )
