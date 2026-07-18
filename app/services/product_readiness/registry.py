from app.services.product_readiness.models import Capability

_CAPABILITIES: dict[str, Capability] = {}


def register(capability: Capability) -> None:
    _CAPABILITIES[capability.id] = capability


def get(capability_id: str) -> Capability | None:
    return _CAPABILITIES.get(capability_id)


def list_all() -> list[Capability]:
    return sorted(
        _CAPABILITIES.values(),
        key=lambda c: c.id,
    )


def clear() -> None:
    _CAPABILITIES.clear()