from copy import deepcopy

from app.services.product_readiness.catalogue import (
    PRODUCT_CAPABILITIES,
)
from app.services.product_readiness.registry import (
    clear,
    register,
)


def bootstrap_product_capabilities() -> int:
    """
    Replace the in-memory registry with the authoritative
    CGMS product capability catalogue.

    The operation is deterministic and idempotent:
    repeated execution always produces the same registry.
    """
    clear()

    for capability in PRODUCT_CAPABILITIES:
        register(deepcopy(capability))

    return len(PRODUCT_CAPABILITIES)