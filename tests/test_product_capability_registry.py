from app.services.product_readiness.models import (
    Capability,
    CapabilityPriority,
    CapabilityStatus,
)

from app.services.product_readiness.registry import (
    clear,
    get,
    list_all,
    register,
)


def setup_function():
    clear()


def test_register_capability():

    capability = Capability(
        id="CAP-001",
        name="Authentication",
        category="Security",
        priority=CapabilityPriority.P0,
        status=CapabilityStatus.IMPLEMENTED,
    )

    register(capability)

    assert get("CAP-001") == capability


def test_registry_returns_sorted():

    register(
        Capability(
            id="CAP-002",
            name="RBAC",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.NOT_STARTED,
        )
    )

    register(
        Capability(
            id="CAP-001",
            name="Authentication",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.IMPLEMENTED,
        )
    )

    capabilities = list_all()

    assert capabilities[0].id == "CAP-001"
    assert capabilities[1].id == "CAP-002"


def test_clear_registry():

    register(
        Capability(
            id="CAP-001",
            name="Authentication",
            category="Security",
            priority=CapabilityPriority.P0,
            status=CapabilityStatus.IMPLEMENTED,
        )
    )

    clear()

    assert list_all() == []