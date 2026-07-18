from app.services.product_readiness.models import (
    Capability,
    CapabilityPriority,
    CapabilityStatus,
)

from app.services.product_readiness.registry import (
    clear,
    register,
)

from app.services.product_readiness.recommendations import (
    generate_recommendations,
)


def setup_function():
    clear()


def test_not_started_generates_recommendation():

    register(
        Capability(
            id="CAP-001",
            name="Authentication",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.NOT_STARTED,
        )
    )

    recommendations = generate_recommendations()

    assert len(recommendations) == 1
    assert recommendations[0].title == "Implement Authentication"


def test_in_progress_generates_completion_recommendation():

    register(
        Capability(
            id="CAP-002",
            name="RBAC",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.IN_PROGRESS,
        )
    )

    recommendations = generate_recommendations()

    assert recommendations[0].title == "Complete RBAC"


def test_implemented_without_tests_generates_test_recommendation():

    register(
        Capability(
            id="CAP-003",
            name="Timeline",
            category="Memory",
            priority=CapabilityPriority.P1,
            status=CapabilityStatus.IMPLEMENTED,
        )
    )

    recommendations = generate_recommendations()

    assert recommendations[0].title == "Test Timeline"


def test_tested_without_security_review_generates_security_review():

    register(
        Capability(
            id="CAP-004",
            name="Semantic Search",
            category="Intelligence",
            priority=CapabilityPriority.P1,
            status=CapabilityStatus.TESTED,
        )
    )

    recommendations = generate_recommendations()

    assert recommendations[0].title == "Security review for Semantic Search"


def test_production_ready_generates_no_recommendation():

    register(
        Capability(
            id="CAP-005",
            name="Memory Engine",
            category="Memory",
            priority=CapabilityPriority.P1,
            status=CapabilityStatus.PRODUCTION_READY,
            tests_passing=True,
            security_reviewed=True,
        )
    )

    recommendations = generate_recommendations()

    assert recommendations == []