from datetime import datetime, timezone
from enum import Enum
from statistics import fmean

from pydantic import BaseModel

from app.services.product_readiness.assessment import (
    ProductAssessment,
    assess_product,
)
from app.services.product_readiness.bootstrap import (
    bootstrap_product_capabilities,
)
from app.services.product_readiness.models import (
    Capability,
    CapabilityPriority,
    CapabilityStatus,
)
from app.services.product_readiness.recommendations import (
    generate_recommendations,
)
from app.services.product_readiness.registry import list_all
from app.services.product_readiness.scoring import capability_score


EXPECTED_CAPABILITY_IDS = frozenset(
    f"CAP-{number:03d}"
    for number in range(1, 39)
)

PILOT_READY_STATUSES = {
    CapabilityStatus.PILOT_READY,
    CapabilityStatus.PRODUCTION_READY,
}


class GateMode(str, Enum):
    STANDARD = "standard"
    STRICT = "strict"


class GateCheck(BaseModel):
    check_id: str
    passed: bool
    expected: str
    actual: str
    message: str


class CapabilityGap(BaseModel):
    capability_id: str
    name: str
    category: str
    priority: str
    status: str
    score: int
    required_for_mlp: bool
    required_for_pilot: bool
    reason: str


class ProductReadinessGateReport(BaseModel):
    schema_version: str = "1.0"
    system: str = "CGMS"

    generated_at: datetime
    mode: GateMode
    passed: bool

    assessment: ProductAssessment
    pilot_scope_score: int
    recommendation_count: int

    checks: list[GateCheck]
    p0_blockers: list[CapabilityGap]
    pilot_scope_gaps: list[CapabilityGap]


def _is_pilot_ready(
    capability: Capability,
) -> bool:
    return capability.status in PILOT_READY_STATUSES


def _capability_gap(
    capability: Capability,
    reason: str,
) -> CapabilityGap:
    return CapabilityGap(
        capability_id=capability.id,
        name=capability.name,
        category=capability.category,
        priority=capability.priority.value,
        status=capability.status.value,
        score=capability_score(capability),
        required_for_mlp=capability.required_for_mlp,
        required_for_pilot=capability.required_for_pilot,
        reason=reason,
    )


def _pilot_scope_score(
    capabilities: list[Capability],
) -> int:
    pilot_capabilities = [
        capability
        for capability in capabilities
        if capability.required_for_pilot
    ]

    if not pilot_capabilities:
        return 0

    return round(
        fmean(
            capability_score(capability)
            for capability in pilot_capabilities
        )
    )


def run_product_readiness_gate(
    mode: GateMode = GateMode.STANDARD,
    minimum_overall_score: int = 25,
    expected_capability_count: int = 38,
) -> ProductReadinessGateReport:
    """
    Bootstrap the authoritative CGMS catalogue and evaluate
    product-readiness CI controls.

    Standard mode protects the approved readiness baseline.

    Strict mode additionally requires all P0 and pilot-scope
    capabilities to reach pilot-ready or production-ready status.
    """
    bootstrap_product_capabilities()

    capabilities = list_all()
    assessment = assess_product()

    capability_ids = [
        capability.id
        for capability in capabilities
    ]

    unique_capability_ids = set(capability_ids)

    p0_blockers = [
        _capability_gap(
            capability,
            (
                "P0 commercial blocker has not reached "
                "pilot-ready status."
            ),
        )
        for capability in capabilities
        if (
            capability.priority == CapabilityPriority.P0
            and not _is_pilot_ready(capability)
        )
    ]

    pilot_scope_gaps = [
        _capability_gap(
            capability,
            (
                "Pilot-required capability has not reached "
                "pilot-ready status."
            ),
        )
        for capability in capabilities
        if (
            capability.required_for_pilot
            and not _is_pilot_ready(capability)
        )
    ]

    pilot_score = _pilot_scope_score(capabilities)

    checks = [
        GateCheck(
            check_id="catalogue-count",
            passed=(
                len(capabilities)
                == expected_capability_count
            ),
            expected=str(expected_capability_count),
            actual=str(len(capabilities)),
            message=(
                "Authoritative capability catalogue count "
                "must remain stable."
            ),
        ),
        GateCheck(
            check_id="catalogue-identifiers",
            passed=(
                unique_capability_ids
                == EXPECTED_CAPABILITY_IDS
            ),
            expected="CAP-001 through CAP-038",
            actual=(
                f"{len(unique_capability_ids)} unique IDs"
            ),
            message=(
                "The capability catalogue must contain the "
                "complete approved identifier set."
            ),
        ),
        GateCheck(
            check_id="duplicate-identifiers",
            passed=(
                len(capability_ids)
                == len(unique_capability_ids)
            ),
            expected="No duplicate capability IDs",
            actual=(
                str(
                    len(capability_ids)
                    - len(unique_capability_ids)
                )
                + " duplicates"
            ),
            message=(
                "Every capability identifier must be unique."
            ),
        ),
        GateCheck(
            check_id="overall-readiness-baseline",
            passed=(
                assessment.overall_score
                >= minimum_overall_score
            ),
            expected=(
                f">= {minimum_overall_score}%"
            ),
            actual=(
                f"{assessment.overall_score}%"
            ),
            message=(
                "Overall readiness must not regress below "
                "the approved baseline."
            ),
        ),
        GateCheck(
            check_id="category-assessment",
            passed=bool(
                assessment.category_scores
            ),
            expected="At least one category score",
            actual=(
                str(
                    len(
                        assessment.category_scores
                    )
                )
                + " category scores"
            ),
            message=(
                "Category readiness evidence must be generated."
            ),
        ),
    ]

    if mode == GateMode.STRICT:
        checks.extend(
            [
                GateCheck(
                    check_id="p0-release-blockers",
                    passed=not p0_blockers,
                    expected="0 unresolved P0 blockers",
                    actual=(
                        str(len(p0_blockers))
                        + " unresolved P0 blockers"
                    ),
                    message=(
                        "Strict release mode prohibits "
                        "unresolved P0 commercial blockers."
                    ),
                ),
                GateCheck(
                    check_id="pilot-scope-readiness",
                    passed=not pilot_scope_gaps,
                    expected=(
                        "All pilot-required capabilities "
                        "are pilot-ready"
                    ),
                    actual=(
                        str(len(pilot_scope_gaps))
                        + " pilot-scope gaps"
                    ),
                    message=(
                        "Every pilot-required capability must "
                        "reach pilot-ready or production-ready "
                        "status."
                    ),
                ),
                GateCheck(
                    check_id="pilot-scope-score",
                    passed=pilot_score >= 95,
                    expected=">= 95%",
                    actual=f"{pilot_score}%",
                    message=(
                        "The pilot capability scope must meet "
                        "the pilot-ready scoring threshold."
                    ),
                ),
            ]
        )

    return ProductReadinessGateReport(
        generated_at=datetime.now(timezone.utc),
        mode=mode,
        passed=all(
            check.passed
            for check in checks
        ),
        assessment=assessment,
        pilot_scope_score=pilot_score,
        recommendation_count=len(
            generate_recommendations()
        ),
        checks=checks,
        p0_blockers=p0_blockers,
        pilot_scope_gaps=pilot_scope_gaps,
    )
