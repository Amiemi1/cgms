import pytest

from app.services.orchestration.domain_event import DomainEvent
from app.services.orchestration.event_bus import EnterpriseEventBus
from app.services.orchestration.event_registry import EventRegistry


def sync_subscriber(event: DomainEvent) -> None:
    assert event.event_name == "memory.created"


async def async_subscriber(event: DomainEvent) -> None:
    assert event.event_name == "memory.created"


def failing_subscriber(event: DomainEvent) -> None:
    raise RuntimeError("subscriber failed")


@pytest.mark.anyio
async def test_event_bus_publishes_to_registered_subscriber():
    registry = EventRegistry()
    registry.subscribe("memory.created", sync_subscriber)

    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={"memory_id": 1},
    )

    result = await bus.publish(event)

    assert result.success is True
    assert result.subscriber_count == 1
    assert result.successful_subscribers == ["sync_subscriber"]
    assert result.failed_subscribers == []


@pytest.mark.anyio
async def test_event_bus_supports_async_subscribers():
    registry = EventRegistry()
    registry.subscribe("memory.created", async_subscriber)

    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={},
    )

    result = await bus.publish(event)

    assert result.success is True
    assert result.successful_subscribers == ["async_subscriber"]


@pytest.mark.anyio
async def test_event_bus_supports_multiple_subscribers():
    registry = EventRegistry()
    registry.subscribe("memory.created", sync_subscriber)
    registry.subscribe("memory.created", async_subscriber)

    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={},
    )

    result = await bus.publish(event)

    assert result.subscriber_count == 2
    assert result.success is True


@pytest.mark.anyio
async def test_event_bus_isolates_subscriber_failures():
    registry = EventRegistry()
    registry.subscribe("memory.created", failing_subscriber)
    registry.subscribe("memory.created", sync_subscriber)

    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={},
    )

    result = await bus.publish(event)

    assert result.success is False
    assert result.subscriber_count == 2
    assert result.failed_subscribers == ["failing_subscriber"]
    assert result.successful_subscribers == ["sync_subscriber"]
    assert len(result.errors) == 1


@pytest.mark.anyio
async def test_event_bus_handles_event_with_no_subscribers():
    registry = EventRegistry()
    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={},
    )

    result = await bus.publish(event)

    assert result.success is True
    assert result.subscriber_count == 0
    assert result.successful_subscribers == []
    assert result.failed_subscribers == []

@pytest.mark.anyio
async def test_event_bus_returns_observability_metadata():
    registry = EventRegistry()
    registry.subscribe("memory.created", sync_subscriber)

    bus = EnterpriseEventBus(registry)

    event = DomainEvent(
        event_name="memory.created",
        source="test",
        payload={},
        correlation_id="corr-123",
    )

    result = await bus.publish(event)

    assert result.started_at is not None
    assert result.completed_at is not None
    assert result.duration_ms is not None
    assert result.duration_ms >= 0
    assert result.correlation_id == "corr-123"
    assert result.event_version == 1