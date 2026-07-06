from app.main import startup_event_bus
from app.services.memory_intelligence.subscribers import (
    memory_intelligence_subscriber,
)
from app.services.orchestration import bootstrap
from app.services.orchestration.contracts.memory_events import MemoryEventName
from app.services.orchestration.event_registry import DEFAULT_EVENT_REGISTRY


def test_app_startup_bootstraps_event_bus():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    startup_event_bus()

    subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(
        MemoryEventName.CREATED
    )

    assert memory_intelligence_subscriber in subscribers