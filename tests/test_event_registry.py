import pytest

from app.services.orchestration.domain_event import DomainEvent
from app.services.orchestration.event_registry import EventRegistry


def subscriber_one(event: DomainEvent) -> None:
    pass


def subscriber_two(event: DomainEvent) -> None:
    pass


def test_subscribe_registers_subscriber():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)

    subscribers = registry.get_subscribers("memory.created")

    assert subscribers == [subscriber_one]


def test_subscribe_registers_multiple_subscribers():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)
    registry.subscribe("memory.created", subscriber_two)

    subscribers = registry.get_subscribers("memory.created")

    assert subscribers == [subscriber_one, subscriber_two]


def test_subscribe_prevents_duplicate_registration():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)
    registry.subscribe("memory.created", subscriber_one)

    subscribers = registry.get_subscribers("memory.created")

    assert subscribers == [subscriber_one]
    assert registry.count("memory.created") == 1


def test_unsubscribe_removes_subscriber():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)

    registry.unsubscribe("memory.created", subscriber_one)

    assert registry.get_subscribers("memory.created") == []
    assert registry.count("memory.created") == 0


def test_unsubscribe_missing_subscriber_is_safe():
    registry = EventRegistry()

    registry.unsubscribe("memory.created", subscriber_one)

    assert registry.get_subscribers("memory.created") == []


def test_unknown_event_returns_empty_list():
    registry = EventRegistry()

    assert registry.get_subscribers("memory.created") == []


def test_get_subscribers_returns_copy():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)

    subscribers = registry.get_subscribers("memory.created")

    subscribers.append(subscriber_two)

    assert registry.get_subscribers("memory.created") == [
        subscriber_one
    ]


def test_clear_removes_all_subscribers():
    registry = EventRegistry()

    registry.subscribe("memory.created", subscriber_one)
    registry.subscribe("runtime.command_executed", subscriber_two)

    registry.clear()

    assert registry.count() == 0
    assert registry.registered_events() == []


def test_registered_events_returns_sorted_event_names():
    registry = EventRegistry()

    registry.subscribe("workspace.created", subscriber_one)
    registry.subscribe("memory.created", subscriber_two)

    assert registry.registered_events() == [
        "memory.created",
        "workspace.created",
    ]


def test_invalid_event_name_raises_value_error():
    registry = EventRegistry()

    with pytest.raises(ValueError):
        registry.subscribe("memory", subscriber_one)


def test_empty_event_name_raises_value_error():
    registry = EventRegistry()

    with pytest.raises(ValueError):
        registry.subscribe("", subscriber_one)