from app.services.orchestration.contracts.memory_events import (
    MemoryEventName,
    memory_created_event,
    memory_priority_changed_event,
    memory_updated_event,
)


def test_memory_event_names_are_canonical():
    assert MemoryEventName.CREATED == "memory.created"
    assert MemoryEventName.UPDATED == "memory.updated"
    assert MemoryEventName.PRIORITY_CHANGED == "memory.priority_changed"


def test_memory_created_event_factory():
    event = memory_created_event(
        memory_id=1,
        source="memory_service",
        workspace_id="workspace-1",
        actor_id="user-1",
        memory_type="task",
        priority="high",
    )

    assert event.event_name == "memory.created"
    assert event.source == "memory_service"
    assert event.workspace_id == "workspace-1"
    assert event.actor_id == "user-1"
    assert event.payload["memory_id"] == 1
    assert event.payload["memory_type"] == "task"
    assert event.payload["priority"] == "high"


def test_memory_updated_event_factory():
    event = memory_updated_event(
        memory_id=2,
        source="memory_service",
        changed_fields=["status", "priority"],
    )

    assert event.event_name == "memory.updated"
    assert event.payload["memory_id"] == 2
    assert event.payload["changed_fields"] == ["status", "priority"]


def test_memory_priority_changed_event_factory():
    event = memory_priority_changed_event(
        memory_id=3,
        source="memory_service",
        old_priority="low",
        new_priority="high",
    )

    assert event.event_name == "memory.priority_changed"
    assert event.payload["memory_id"] == 3
    assert event.payload["old_priority"] == "low"
    assert event.payload["new_priority"] == "high"