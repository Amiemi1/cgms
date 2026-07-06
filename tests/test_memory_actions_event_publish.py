from app.dashboard.routes import memory_actions


class FakeMemory:
    def __init__(self, memory_id: int, priority: int):
        self.id = memory_id
        self.priority = priority


class FakeSession:
    def __init__(self):
        self.memory = FakeMemory(memory_id=1, priority=2)
        self.committed = False
        self.refreshed = False
        self.closed = False

    def get(self, model, memory_id):
        return self.memory

    def add(self, memory):
        self.memory = memory

    def commit(self):
        self.committed = True

    def refresh(self, memory):
        self.refreshed = True

    def close(self):
        self.closed = True


def test_update_priority_publishes_memory_priority_changed_event(monkeypatch):
    fake_session = FakeSession()
    captured = {}

    monkeypatch.setattr(
        memory_actions,
        "SessionLocal",
        lambda: fake_session,
    )

    def fake_publish_memory_event(event):
        captured["event"] = event

    monkeypatch.setattr(
        memory_actions,
        "publish_memory_event",
        fake_publish_memory_event,
    )

    response = memory_actions.update_priority(
        memory_id=1,
        priority=5,
    )

    event = captured["event"]

    assert fake_session.committed is True
    assert fake_session.refreshed is True
    assert fake_session.closed is True

    assert event.event_name == "memory.priority_changed"
    assert event.source == "memory_actions.update_priority"
    assert event.payload["memory_id"] == 1
    assert event.payload["old_priority"] == 2
    assert event.payload["new_priority"] == 5

    assert response["event_published"] is True
    assert response["event_name"] == "memory.priority_changed"
    assert response["old_priority"] == 2
    assert response["priority"] == 5


def test_update_priority_returns_error_when_memory_not_found(monkeypatch):
    class EmptySession:
        def __init__(self):
            self.closed = False

        def get(self, model, memory_id):
            return None

        def close(self):
            self.closed = True

    empty_session = EmptySession()

    monkeypatch.setattr(
        memory_actions,
        "SessionLocal",
        lambda: empty_session,
    )

    response = memory_actions.update_priority(
        memory_id=999,
        priority=5,
    )

    assert response == {"error": "Memory not found"}
    assert empty_session.closed is True