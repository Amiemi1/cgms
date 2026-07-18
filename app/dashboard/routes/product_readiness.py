from fastapi import APIRouter, HTTPException

from app.services.product_readiness.assessment import (
    ProductAssessment,
    assess_product,
)
from app.services.product_readiness.models import Capability
from app.services.product_readiness.recommendations import (
    Recommendation,
    generate_recommendations,
)
from app.services.product_readiness.registry import (
    get as get_capability,
    list_all,
)
from app.services.product_readiness.scoring import (
    category_scores as calculate_category_scores,
)

router = APIRouter(
    prefix="/product-readiness",
    tags=["Product Readiness"],
)


@router.get(
    "/assessment",
    response_model=ProductAssessment,
)
def read_product_assessment() -> ProductAssessment:
    """
    Return the current product readiness assessment.
    """
    return assess_product()


@router.get(
    "/capabilities",
    response_model=list[Capability],
)
def read_capabilities() -> list[Capability]:
    """
    Return all registered capabilities.
    """
    return list_all()


@router.get(
    "/capabilities/{capability_id}",
    response_model=Capability,
)
def read_capability(capability_id: str) -> Capability:
    """
    Return a single capability.
    """
    capability = get_capability(capability_id)

    if capability is None:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_id}' not found.",
        )

    return capability


@router.get(
    "/recommendations",
    response_model=list[Recommendation],
)
def read_recommendations() -> list[Recommendation]:
    """
    Return prioritized engineering recommendations.
    """
    return generate_recommendations()


@router.get(
    "/categories",
    response_model=dict[str, int],
)
def read_category_scores() -> dict[str, int]:
    """
    Return readiness scores grouped by category.
    """
    return calculate_category_scores()