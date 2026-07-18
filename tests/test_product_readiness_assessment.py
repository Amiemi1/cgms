from app.services.product_readiness.models import (
    Capability,
    CapabilityPriority,
    CapabilityStatus,
)

from app.services.product_readiness.registry import (
    clear,
    register,
)

from app.services.product_readiness.assessment import (
    assess_product,
)


def setup_function():

    clear()


def test_empty_assessment():

    assessment = assess_product()

    assert assessment.total_capabilities == 0
    assert assessment.overall_score == 0


def test_assessment_counts():

    register(
        Capability(
            id="CAP-001",
            name="Authentication",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.PRODUCTION_READY,
        )
    )

    register(
        Capability(
            id="CAP-002",
            name="RBAC",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.PILOT_READY,
        )
    )

    register(
        Capability(
            id="CAP-003",
            name="Timeline",
            category="Memory",
            priority=CapabilityPriority.P1,
            status=CapabilityStatus.IMPLEMENTED,
        )
    )

    register(
        Capability(
            id="CAP-004",
            name="Knowledge Graph",
            category="Intelligence",
            priority=CapabilityPriority.P3,
            status=CapabilityStatus.NOT_STARTED,
        )
    )

    assessment = assess_product()

    assert assessment.total_capabilities == 4

    assert assessment.production_ready == 1

    assert assessment.pilot_ready == 1

    assert assessment.implemented == 1

    assert assessment.not_started == 1


def test_category_scores_are_present():

    register(
        Capability(
            id="CAP-001",
            name="Authentication",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.PRODUCTION_READY,
        )
    )

    assessment = assess_product()

    assert "Security" in assessment.category_scores