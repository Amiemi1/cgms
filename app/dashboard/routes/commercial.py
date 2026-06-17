from fastapi import APIRouter

from app.services.commercial.billing_meter import (
    usage_meter
)

from app.services.commercial.plan_registry import (
    get_active_plan,
    set_plan
)

from app.services.commercial.plan_registry import (
    get_active_plan,
    set_plan,
    enforce_plan_limits
)

router = APIRouter()


@router.get(
    "/commercial/usage"
)
def usage():

    return usage_meter()

@router.get(
    "/commercial/plan"
)
def plan():

    return get_active_plan()


@router.post(
    "/commercial/plan"
)
def update_plan(
    payload: dict
):

    return set_plan(
        payload.get(
            "plan"
        )
    )

@router.get("/commercial/enforcement")
def commercial_enforcement():

    return enforce_plan_limits()