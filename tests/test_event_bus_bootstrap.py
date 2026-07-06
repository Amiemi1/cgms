from app.services.memory_intelligence.subscribers import (
    memory_intelligence_subscriber,
)
from app.services.orchestration import bootstrap
from app.services.orchestration.bootstrap import bootstrap_event_bus
from app.services.orchestration.contracts.memory_events import MemoryEventName
from app.services.orchestration.event_registry import DEFAULT_EVENT_REGISTRY


def test_bootstrap_registers_memory_intelligence_subscriber():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    bootstrap_event_bus()

    subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(
        MemoryEventName.CREATED
    )

    assert memory_intelligence_subscriber in subscribers


def test_bootstrap_is_idempotent():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    bootstrap_event_bus()
    bootstrap_event_bus()

    subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(
        MemoryEventName.CREATED
    )

    assert subscribers.count(memory_intelligence_subscriber) == 1


def test_bootstrap_registers_supported_memory_events():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    bootstrap_event_bus()

    expected_events = [
        MemoryEventName.CREATED,
        MemoryEventName.UPDATED,
        MemoryEventName.REOPENED,
        MemoryEventName.RESTORED,
        MemoryEventName.PRIORITY_CHANGED,
    ]

    for event_name in expected_events:
        subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(event_name)
        assert memory_intelligence_subscriber in subscribers