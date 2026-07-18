from app.services.product_readiness.models import (
    Capability,
    CapabilityPriority,
    CapabilityStatus,
)

from app.services.product_readiness.registry import (
    clear,
    register,
)

from app.services.product_readiness.scoring import (
    capability_score,
    category_scores,
    overall_score,
)


def setup_function():
    clear()


def test_capability_score():

    capability = Capability(
        id="CAP-001",
        name="Authentication",
        category="Security",
        priority=CapabilityPriority.P0,
        status=CapabilityStatus.IMPLEMENTED,
        tests_passing=True,
        documented=True,
    )

    assert capability_score(capability) == 60


def test_category_scores():

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
            status=CapabilityStatus.HARDENED,
        )
    )

    scores = category_scores()

    assert scores["Security"] == 92


def test_overall_score():

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
            name="Memory",
            category="Memory",
            priority=CapabilityPriority.P1,
            status=CapabilityStatus.IMPLEMENTED,
        )
    )

    assert overall_score() == 75


def test_empty_registry_returns_zero():

    assert overall_score() == 0