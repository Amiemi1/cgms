import pytest

from app.services.orchestration.bootstrap import bootstrap_event_bus
from app.services.orchestration.contracts.memory_events import (
    MemoryEventName,
    memory_created_event,
)
from app.services.orchestration.event_bus import DEFAULT_EVENT_BUS
from app.services.orchestration.event_registry import DEFAULT_EVENT_REGISTRY
from app.services.orchestration import bootstrap
from app.services.orchestration.subscribers.audit_subscriber import (
    AUDIT_EVENT_LOG,
    audit_subscriber,
    clear_audit_event_log,
)


def test_audit_subscriber_records_event():
    clear_audit_event_log()

    event = memory_created_event(
        memory_id=1,
        source="test",
        workspace_id="workspace-1",
        actor_id="user-1",
        correlation_id="corr-1",
    )

    audit_subscriber(event)

    assert len(AUDIT_EVENT_LOG) == 1

    record = AUDIT_EVENT_LOG[0]

    assert record["event_id"] == event.event_id
    assert record["event_name"] == "memory.created"
    assert record["source"] == "test"
    assert record["workspace_id"] == "workspace-1"
    assert record["actor_id"] == "user-1"
    assert record["correlation_id"] == "corr-1"
    assert record["payload"]["memory_id"] == 1


def test_bootstrap_registers_audit_subscriber_for_memory_events():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    bootstrap_event_bus()

    for event_name in MemoryEventName:
        subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(event_name)
        assert audit_subscriber in subscribers


@pytest.mark.anyio
async def test_event_bus_dispatches_to_audit_subscriber():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False
    clear_audit_event_log()

    bootstrap_event_bus()

    event = memory_created_event(
        memory_id=7,
        source="test",
    )

    result = await DEFAULT_EVENT_BUS.publish(event)

    assert result.success is True
    assert "audit_subscriber" in result.successful_subscribers
    assert len(AUDIT_EVENT_LOG) == 1
    assert AUDIT_EVENT_LOG[0]["event_name"] == "memory.created"
    assert AUDIT_EVENT_LOG[0]["payload"]["memory_id"] == 7