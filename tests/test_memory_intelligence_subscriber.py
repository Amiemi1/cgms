from app.services.memory_intelligence import subscribers
from app.services.memory_intelligence.subscribers import (
    memory_intelligence_subscriber,
)
from app.services.orchestration.contracts.memory_events import (
    memory_created_event,
)


def test_memory_intelligence_subscriber_processes_memory_created(monkeypatch):
    captured = {}

    def fake_process_memory_event(event: dict):
        captured.update(event)
        return {"processed": True}

    monkeypatch.setattr(
        subscribers,
        "process_memory_event",
        fake_process_memory_event,
    )

    event = memory_created_event(
        memory_id=123,
        source="test",
    )

    memory_intelligence_subscriber(event)

    assert captured == {
        "event": "MemoryCreated",
        "memory_id": 123,
    }


def test_memory_intelligence_subscriber_ignores_unsupported_event(monkeypatch):
    called = False

    def fake_process_memory_event(event: dict):
        nonlocal called
        called = True

    monkeypatch.setattr(
        subscribers,
        "process_memory_event",
        fake_process_memory_event,
    )

    event = memory_created_event(
        memory_id=123,
        source="test",
    )

    object.__setattr__(event, "event_name", "memory.deleted")

    memory_intelligence_subscriber(event)

    assert called is False