from collections import defaultdict

from app.services.product_readiness.models import (
    Capability,
    CapabilityStatus,
)
from app.services.product_readiness.registry import (
    list_all,
)

STATUS_SCORE = {
    CapabilityStatus.NOT_STARTED: 0,
    CapabilityStatus.IN_PROGRESS: 20,
    CapabilityStatus.IMPLEMENTED: 50,
    CapabilityStatus.TESTED: 70,
    CapabilityStatus.HARDENED: 85,
    CapabilityStatus.PILOT_READY: 95,
    CapabilityStatus.PRODUCTION_READY: 100,
}


def capability_score(capability: Capability) -> int:
    """
    Calculate readiness score for a single capability.
    """
    score = STATUS_SCORE[capability.status]

    if capability.tests_passing:
        score += 5

    if capability.security_reviewed:
        score += 5

    if capability.ux_complete:
        score += 5

    if capability.documented:
        score += 5

    return min(score, 100)


def category_scores() -> dict[str, int]:
    """
    Average readiness by category.
    """

    grouped = defaultdict(list)

    for capability in list_all():
        grouped[capability.category].append(
            capability_score(capability)
        )

    return {
        category: round(sum(scores) / len(scores))
        for category, scores in grouped.items()
    }


def overall_score() -> int:
    """
    Overall CGMS readiness.
    """

    capabilities = list_all()

    if not capabilities:
        return 0

    scores = [
        capability_score(c)
        for c in capabilities
    ]

    return round(sum(scores) / len(scores))