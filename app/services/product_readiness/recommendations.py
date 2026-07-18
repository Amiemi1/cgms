from pydantic import BaseModel

from app.services.product_readiness.registry import list_all
from app.services.product_readiness.models import CapabilityStatus


class Recommendation(BaseModel):
    capability_id: str
    title: str
    priority: str
    reason: str


def generate_recommendations() -> list[Recommendation]:

    recommendations = []

    for capability in list_all():

        if capability.status == CapabilityStatus.NOT_STARTED:

            recommendations.append(
                Recommendation(
                    capability_id=capability.id,
                    title=f"Implement {capability.name}",
                    priority=capability.priority.value,
                    reason="Capability has not been started.",
                )
            )

        elif capability.status == CapabilityStatus.IN_PROGRESS:

            recommendations.append(
                Recommendation(
                    capability_id=capability.id,
                    title=f"Complete {capability.name}",
                    priority=capability.priority.value,
                    reason="Capability is partially implemented.",
                )
            )

        elif (
            capability.status == CapabilityStatus.IMPLEMENTED
            and not capability.tests_passing
        ):

            recommendations.append(
                Recommendation(
                    capability_id=capability.id,
                    title=f"Test {capability.name}",
                    priority=capability.priority.value,
                    reason="Implementation exists but regression tests are incomplete.",
                )
            )

        elif (
            capability.status == CapabilityStatus.TESTED
            and not capability.security_reviewed
        ):

            recommendations.append(
                Recommendation(
                    capability_id=capability.id,
                    title=f"Security review for {capability.name}",
                    priority=capability.priority.value,
                    reason="Security review has not been completed.",
                )
            )

    return sorted(
        recommendations,
        key=lambda r: (r.priority, r.capability_id),
    )