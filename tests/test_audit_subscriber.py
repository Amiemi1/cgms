from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.db.models.audit_record import AuditRecord
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.services.orchestration import bootstrap
from app.services.orchestration.bootstrap import bootstrap_event_bus
from app.services.orchestration.contracts.memory_events import (
    MemoryEventName,
    memory_created_event,
)
from app.services.orchestration.event_bus import DEFAULT_EVENT_BUS
from app.services.orchestration.domain_event import DomainEvent
from app.services.orchestration.event_registry import DEFAULT_EVENT_REGISTRY
from app.services.orchestration.subscribers import (
    audit_subscriber as audit_subscriber_module,
)
from app.services.orchestration.subscribers.audit_subscriber import (
    audit_subscriber,
)
from app.services.persistence.audit_store import (
    PersistentAuditStore,
)


def _isolated_store():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
    User.__table__.create(
        engine,
        checkfirst=True,
    )
    Workspace.__table__.create(
        engine,
        checkfirst=True,
    )
    AuditRecord.__table__.create(
        engine,
        checkfirst=True,
    )

    with Session(engine) as session:
        session.add(
            Workspace(
                id="workspace-1",
                name="Workspace One",
                status="active",
            )
        )
        session.commit()

    return (
        engine,
        PersistentAuditStore(
            lambda: Session(engine)
        ),
    )


def test_audit_subscriber_persists_domain_event(
    monkeypatch: pytest.MonkeyPatch,
):
    engine, store = _isolated_store()
    monkeypatch.setattr(
        audit_subscriber_module,
        "get_persistent_audit_store",
        lambda: store,
    )

    event = memory_created_event(
        memory_id=1,
        source="test",
        workspace_id="workspace-1",
        actor_id="user-1",
        correlation_id="corr-1",
    )

    audit_subscriber(event)

    records = store.list_for_workspace(
        "workspace-1"
    )

    assert len(records) == 1
    record = records[0]
    assert record.origin_id == (
        f"domain_event:{event.event_id}"
    )
    assert record.category == "domain_event"
    assert record.action == "memory.created"
    assert record.source == "test"
    assert record.workspace_id == "workspace-1"
    assert record.actor_id == "user-1"
    assert record.correlation_id == "corr-1"
    assert record.details["payload"]["memory_id"] == 1

    engine.dispose()


def test_bootstrap_registers_audit_subscriber_for_memory_events():
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False

    bootstrap_event_bus()

    for event_name in MemoryEventName:
        subscribers = DEFAULT_EVENT_REGISTRY.get_subscribers(event_name)
        assert audit_subscriber in subscribers


@pytest.mark.anyio
async def test_event_bus_dispatches_to_persistent_audit_subscriber(
    monkeypatch: pytest.MonkeyPatch,
):
    engine, store = _isolated_store()
    monkeypatch.setattr(
        audit_subscriber_module,
        "get_persistent_audit_store",
        lambda: store,
    )
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False
    bootstrap_event_bus()

    event = memory_created_event(
        memory_id=7,
        source="test",
        workspace_id="workspace-1",
    )

    result = await DEFAULT_EVENT_BUS.publish(event)

    assert result.success is True
    assert "audit_subscriber" in result.successful_subscribers

    restarted_store = PersistentAuditStore(
        lambda: Session(engine)
    )
    records = restarted_store.list_for_workspace(
        "workspace-1"
    )
    assert len(records) == 1
    assert records[0].action == "memory.created"
    assert records[0].details["payload"]["memory_id"] == 7

    engine.dispose()


@pytest.mark.anyio
async def test_global_audit_subscription_covers_non_memory_events(
    monkeypatch: pytest.MonkeyPatch,
):
    engine, store = _isolated_store()
    monkeypatch.setattr(
        audit_subscriber_module,
        "get_persistent_audit_store",
        lambda: store,
    )
    DEFAULT_EVENT_REGISTRY.clear()
    bootstrap._BOOTSTRAPPED = False
    bootstrap_event_bus()
    event = DomainEvent(
        event_name="workspace.suspended",
        source="workspace_control",
        workspace_id="workspace-1",
        actor_id="admin-1",
        payload={
            "workspace_id": "workspace-1",
        },
    )

    result = await DEFAULT_EVENT_BUS.publish(
        event
    )

    assert result.success is True
    records = store.list_for_workspace(
        "workspace-1"
    )
    assert len(records) == 1
    assert records[0].action == (
        "workspace.suspended"
    )
    assert records[0].subject_type == (
        "workspace"
    )

    engine.dispose()


def test_domain_event_origin_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
):
    engine, store = _isolated_store()
    monkeypatch.setattr(
        audit_subscriber_module,
        "get_persistent_audit_store",
        lambda: store,
    )
    event = memory_created_event(
        memory_id=9,
        source="test",
        workspace_id="workspace-1",
    )

    audit_subscriber(event)
    audit_subscriber(event)

    assert len(
        store.list_for_workspace(
            "workspace-1"
        )
    ) == 1

    engine.dispose()
