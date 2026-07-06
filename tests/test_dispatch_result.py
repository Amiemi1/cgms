from app.services.orchestration.dispatch_result import DispatchResult


def test_dispatch_result_success_property():
    result = DispatchResult(
        event_id="event-1",
        event_name="memory.created",
        subscriber_count=1,
        successful_subscribers=["handler"],
    )

    assert result.success is True
    assert result.success_count == 1
    assert result.failure_count == 0


def test_dispatch_result_failure_property():
    result = DispatchResult(
        event_id="event-1",
        event_name="memory.created",
        subscriber_count=1,
        failed_subscribers=["handler"],
        errors=["handler: failed"],
    )

    assert result.success is False
    assert result.success_count == 0
    assert result.failure_count == 1


def test_dispatch_result_serialization():
    result = DispatchResult(
        event_id="event-1",
        event_name="memory.created",
        event_version=1,
        subscriber_count=1,
        successful_subscribers=["handler"],
        correlation_id="corr-1",
    )

    data = result.to_dict()

    assert data["event_id"] == "event-1"
    assert data["event_name"] == "memory.created"
    assert data["event_version"] == 1
    assert data["success"] is True
    assert data["correlation_id"] == "corr-1"