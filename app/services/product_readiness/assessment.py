from pydantic import BaseModel

from app.services.product_readiness.scoring import (
    category_scores,
    overall_score,
)
from app.services.product_readiness.registry import (
    list_all,
)


class ProductAssessment(BaseModel):

    total_capabilities: int

    overall_score: int

    category_scores: dict[str, int]

    production_ready: int

    pilot_ready: int

    implemented: int

    in_progress: int

    not_started: int


def assess_product() -> ProductAssessment:

    capabilities = list_all()

    production_ready = 0
    pilot_ready = 0
    implemented = 0
    in_progress = 0
    not_started = 0

    for capability in capabilities:

        status = capability.status.value

        if status == "production_ready":
            production_ready += 1

        elif status == "pilot_ready":
            pilot_ready += 1

        elif status in (
            "implemented",
            "tested",
            "hardened",
        ):
            implemented += 1

        elif status == "in_progress":
            in_progress += 1

        else:
            not_started += 1

    return ProductAssessment(

        total_capabilities=len(capabilities),

        overall_score=overall_score(),

        category_scores=category_scores(),

        production_ready=production_ready,

        pilot_ready=pilot_ready,

        implemented=implemented,

        in_progress=in_progress,

        not_started=not_started,
    )