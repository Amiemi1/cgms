from app.services.orchestration.domain_event import DomainEvent


def test_event_creation():

    event = DomainEvent(
        event_name="memory.created",
        source="memory_service",
        payload={"memory_id": 10},
    )

    assert event.event_name == "memory.created"

    assert event.source == "memory_service"

    assert event.payload["memory_id"] == 10

    assert event.event_version == 1

    assert event.event_id is not None


def test_bounded_context():

    event = DomainEvent(
        event_name="workspace.created",
        source="workspace",
        payload={},
    )

    assert event.bounded_context == "workspace"


def test_action():

    event = DomainEvent(
        event_name="memory.completed",
        source="memory",
        payload={},
    )

    assert event.action == "completed"


def test_serialization():

    event = DomainEvent(
        event_name="memory.updated",
        source="memory",
        payload={"id": 5},
    )

    data = event.to_dict()

    assert data["event_name"] == "memory.updated"

    assert data["payload"]["id"] == 5


def test_event_is_immutable():

    event = DomainEvent(
        event_name="memory.created",
        source="memory",
        payload={},
    )

    try:
        event.event_name = "other"
        assert False
    except Exception:
        assert True