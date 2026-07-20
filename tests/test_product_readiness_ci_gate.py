from app.services.product_readiness.ci_gate import (
    EXPECTED_CAPABILITY_IDS,
    GateMode,
    run_product_readiness_gate,
)
from app.services.product_readiness.registry import clear


def setup_function() -> None:
    clear()


def teardown_function() -> None:
    clear()


def test_standard_gate_passes_at_approved_baseline() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STANDARD,
    )

    assert report.passed is True
    assert report.mode == GateMode.STANDARD

    assert report.assessment.total_capabilities == 38
    assert report.assessment.overall_score == 23

    assert report.recommendation_count == 29
    assert report.pilot_scope_score > 0

    assert len(report.p0_blockers) == 5
    assert report.pilot_scope_gaps

    assert all(
        check.passed
        for check in report.checks
    )


def test_strict_gate_reports_release_blockers() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STRICT,
    )

    assert report.passed is False
    assert report.mode == GateMode.STRICT

    checks = {
        check.check_id: check
        for check in report.checks
    }

    assert checks["p0-release-blockers"].passed is False
    assert checks["pilot-scope-readiness"].passed is False
    assert checks["pilot-scope-score"].passed is False

    assert len(report.p0_blockers) == 5
    assert len(report.pilot_scope_gaps) > 0
    assert report.pilot_scope_score < 95


def test_standard_gate_detects_readiness_regression() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STANDARD,
        minimum_overall_score=24,
    )

    assert report.passed is False

    baseline_check = next(
        check
        for check in report.checks
        if (
            check.check_id
            == "overall-readiness-baseline"
        )
    )

    assert baseline_check.passed is False
    assert baseline_check.expected == ">= 24%"
    assert baseline_check.actual == "23%"


def test_gate_detects_catalogue_count_mismatch() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STANDARD,
        expected_capability_count=39,
    )

    assert report.passed is False

    count_check = next(
        check
        for check in report.checks
        if check.check_id == "catalogue-count"
    )

    assert count_check.passed is False
    assert count_check.expected == "39"
    assert count_check.actual == "38"


def test_gate_validates_complete_capability_identifier_set() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STANDARD,
    )

    identifier_check = next(
        check
        for check in report.checks
        if (
            check.check_id
            == "catalogue-identifiers"
        )
    )

    assert identifier_check.passed is True
    assert len(EXPECTED_CAPABILITY_IDS) == 38
    assert "CAP-001" in EXPECTED_CAPABILITY_IDS
    assert "CAP-038" in EXPECTED_CAPABILITY_IDS


def test_gate_report_is_machine_serializable() -> None:
    report = run_product_readiness_gate(
        mode=GateMode.STANDARD,
    )

    payload = report.model_dump(
        mode="json",
    )

    assert payload["schema_version"] == "1.0"
    assert payload["system"] == "CGMS"
    assert payload["mode"] == "standard"
    assert payload["passed"] is True

    assert isinstance(
        payload["generated_at"],
        str,
    )

    assert (
        payload["assessment"]["total_capabilities"]
        == 38
    )

    assert isinstance(
        payload["checks"],
        list,
    )

    assert isinstance(
        payload["p0_blockers"],
        list,
    )

    assert isinstance(
        payload["pilot_scope_gaps"],
        list,
    )