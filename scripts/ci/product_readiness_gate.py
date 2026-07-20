from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from app.services.product_readiness.ci_gate import (  # noqa: E402
    GateMode,
    ProductReadinessGateReport,
    run_product_readiness_gate,
)


DEFAULT_ARTIFACT_DIRECTORY = (
    ROOT_DIR / "artifacts" / "product-readiness"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate CGMS product-readiness controls and "
            "generate machine-readable CI evidence."
        ),
    )

    parser.add_argument(
        "--mode",
        choices=[
            GateMode.STANDARD.value,
            GateMode.STRICT.value,
        ],
        default=GateMode.STANDARD.value,
        help=(
            "Gate mode. Standard protects the approved baseline; "
            "strict enforces pilot and release blockers."
        ),
    )

    parser.add_argument(
        "--minimum-overall-score",
        type=int,
        default=23,
        help=(
            "Minimum permitted overall readiness score. "
            "Defaults to the approved 23 percent baseline."
        ),
    )

    parser.add_argument(
        "--expected-capability-count",
        type=int,
        default=38,
        help=(
            "Expected authoritative capability catalogue count."
        ),
    )

    parser.add_argument(
        "--output-directory",
        type=Path,
        default=DEFAULT_ARTIFACT_DIRECTORY,
        help=(
            "Directory for JSON and Markdown readiness evidence."
        ),
    )

    return parser.parse_args()


def build_markdown_summary(
    report: ProductReadinessGateReport,
) -> str:
    status = "PASSED" if report.passed else "FAILED"

    lines = [
        "# CGMS Product Readiness Gate",
        "",
        f"**Result:** {status}",
        f"**Mode:** {report.mode.value}",
        (
            "**Generated:** "
            f"{report.generated_at.isoformat()}"
        ),
        "",
        "## Readiness Summary",
        "",
        (
            f"- Overall readiness: "
            f"{report.assessment.overall_score}%"
        ),
        (
            f"- Pilot-scope readiness: "
            f"{report.pilot_scope_score}%"
        ),
        (
            f"- Registered capabilities: "
            f"{report.assessment.total_capabilities}"
        ),
        (
            f"- Production-ready capabilities: "
            f"{report.assessment.production_ready}"
        ),
        (
            f"- Pilot-ready capabilities: "
            f"{report.assessment.pilot_ready}"
        ),
        (
            f"- Open recommendations: "
            f"{report.recommendation_count}"
        ),
        (
            f"- Unresolved P0 blockers: "
            f"{len(report.p0_blockers)}"
        ),
        (
            f"- Pilot-scope gaps: "
            f"{len(report.pilot_scope_gaps)}"
        ),
        "",
        "## Gate Checks",
        "",
        "| Check | Result | Expected | Actual |",
        "|---|---|---|---|",
    ]

    for check in report.checks:
        result = "PASS" if check.passed else "FAIL"

        lines.append(
            "| "
            f"{check.check_id} | "
            f"{result} | "
            f"{check.expected} | "
            f"{check.actual} |"
        )

    lines.extend(
        [
            "",
            "## P0 Commercial Blockers",
            "",
        ]
    )

    if report.p0_blockers:
        lines.extend(
            [
                "| Capability | Status | Score | Reason |",
                "|---|---|---:|---|",
            ]
        )

        for blocker in report.p0_blockers:
            lines.append(
                "| "
                f"{blocker.capability_id} - {blocker.name} | "
                f"{blocker.status} | "
                f"{blocker.score}% | "
                f"{blocker.reason} |"
            )
    else:
        lines.append("No unresolved P0 blockers.")

    lines.extend(
        [
            "",
            "## Pilot-Scope Gaps",
            "",
        ]
    )

    if report.pilot_scope_gaps:
        lines.extend(
            [
                "| Capability | Priority | Status | Score |",
                "|---|---|---|---:|",
            ]
        )

        for gap in report.pilot_scope_gaps:
            lines.append(
                "| "
                f"{gap.capability_id} - {gap.name} | "
                f"{gap.priority} | "
                f"{gap.status} | "
                f"{gap.score}% |"
            )
    else:
        lines.append(
            "All pilot-required capabilities meet the gate."
        )

    lines.append("")

    return "\n".join(lines)


def write_evidence(
    report: ProductReadinessGateReport,
    output_directory: Path,
) -> tuple[Path, Path]:
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        output_directory
        / "product_readiness_report.json"
    )

    markdown_path = (
        output_directory
        / "product_readiness_summary.md"
    )

    json_path.write_text(
        json.dumps(
            report.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    markdown_summary = build_markdown_summary(report)

    markdown_path.write_text(
        markdown_summary,
        encoding="utf-8",
    )

    github_step_summary = os.getenv(
        "GITHUB_STEP_SUMMARY"
    )

    if github_step_summary:
        with Path(github_step_summary).open(
            "a",
            encoding="utf-8",
        ) as summary_file:
            summary_file.write(markdown_summary)
            summary_file.write("\n")

    return json_path, markdown_path


def print_console_summary(
    report: ProductReadinessGateReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    status = "PASSED" if report.passed else "FAILED"

    print("=" * 64)
    print("CGMS PRODUCT READINESS GATE")
    print("=" * 64)
    print(f"Mode:                  {report.mode.value}")
    print(f"Result:                {status}")
    print(
        "Overall readiness:     "
        f"{report.assessment.overall_score}%"
    )
    print(
        "Pilot-scope readiness: "
        f"{report.pilot_scope_score}%"
    )
    print(
        "Capabilities:           "
        f"{report.assessment.total_capabilities}"
    )
    print(
        "P0 blockers:            "
        f"{len(report.p0_blockers)}"
    )
    print(
        "Pilot-scope gaps:        "
        f"{len(report.pilot_scope_gaps)}"
    )
    print(
        "Recommendations:        "
        f"{report.recommendation_count}"
    )
    print("-" * 64)

    for check in report.checks:
        marker = "PASS" if check.passed else "FAIL"

        print(
            f"[{marker}] "
            f"{check.check_id}: "
            f"{check.actual}"
        )

    print("-" * 64)
    print(f"JSON evidence:     {json_path}")
    print(f"Markdown evidence: {markdown_path}")
    print("=" * 64)


def main() -> int:
    arguments = parse_arguments()

    if not 0 <= arguments.minimum_overall_score <= 100:
        print(
            "ERROR: --minimum-overall-score must be "
            "between 0 and 100.",
            file=sys.stderr,
        )
        return 2

    if arguments.expected_capability_count <= 0:
        print(
            "ERROR: --expected-capability-count must be "
            "greater than zero.",
            file=sys.stderr,
        )
        return 2

    try:
        report = run_product_readiness_gate(
            mode=GateMode(arguments.mode),
            minimum_overall_score=(
                arguments.minimum_overall_score
            ),
            expected_capability_count=(
                arguments.expected_capability_count
            ),
        )

        json_path, markdown_path = write_evidence(
            report=report,
            output_directory=arguments.output_directory,
        )

        print_console_summary(
            report=report,
            json_path=json_path,
            markdown_path=markdown_path,
        )

        return 0 if report.passed else 1

    except Exception as exc:
        print(
            "ERROR: Product Readiness gate could not run: "
            f"{exc}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())