from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import insert
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

import app.services.connectors.event_ingestion as event_ingestion
from app.db.migrations.cap_003_workspace_control import (
    apply_workspace_control,
    validate_workspace_control,
)
from app.db.models.user import User
from app.db.models.workspace import (
    Workspace,
    WorkspaceMembership,
)
from app.db.models.workspace_control import (
    WorkspaceControl,
)
from app.services.auth.application_authorization import (
    MANAGE_USERS,
    required_permission_for_route,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
)
from app.services.workspace.metrics import workspace_metrics
from app.services.workspace.repository import (
    WorkspaceInactiveError,
    WorkspaceRepository,
)


ROOT = Path(__file__).resolve().parents[1]


def _isolated_engine():
    return create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )


def _create_control_schema(engine) -> None:
    User.__table__.create(
        engine,
        checkfirst=True,
    )
    Workspace.__table__.create(
        engine,
        checkfirst=True,
    )
    WorkspaceMembership.__table__.create(
        engine,
        checkfirst=True,
    )
    WorkspaceControl.__table__.create(
        engine,
        checkfirst=True,
    )


def _seed_account(engine, user_id: int = 1) -> None:
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                email=f"user-{user_id}@example.com",
                password_hash="test-only",
            )
        )
        session.commit()


def _repositories(engine):
    session_factory = lambda: Session(engine)
    return (
        WorkspaceRepository(session_factory),
        WorkspaceControlRepository(session_factory),
    )


def test_workspace_creation_establishes_persistent_owner_and_control():
    engine = _isolated_engine()
    _create_control_schema(engine)
    _seed_account(engine)
    workspace_repository, control_repository = (
        _repositories(engine)
    )

    workspace_repository.create_workspace(
        workspace_id="alpha",
        name="Alpha Workspace",
        created_by_user_id=1,
        owner_user_id=1,
    )

    with Session(engine) as session:
        membership = session.exec(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id
                == "alpha",
                WorkspaceMembership.user_id == 1,
            )
        ).one()
        control = session.exec(
            select(WorkspaceControl).where(
                WorkspaceControl.workspace_id
                == "alpha"
            )
        ).one()

    assert membership.status == "active"
    assert control.max_events == 1000

    restarted_workspace_repository, restarted_control_repository = (
        _repositories(engine)
    )
    assert (
        restarted_workspace_repository.require_workspace(
            "alpha"
        ).name
        == "Alpha Workspace"
    )
    assert (
        restarted_control_repository.get_quota(
            "alpha"
        ).max_events
        == 1000
    )


def test_lifecycle_and_quota_changes_survive_repository_restart():
    engine = _isolated_engine()
    _create_control_schema(engine)
    _seed_account(engine)
    workspace_repository, control_repository = (
        _repositories(engine)
    )
    workspace_repository.create_workspace(
        workspace_id="alpha",
        name="Alpha Workspace",
        created_by_user_id=1,
        owner_user_id=1,
    )

    control_repository.set_quota(
        "alpha",
        {
            "maxEvents": 7,
        },
        updated_by_user_id=1,
    )
    suspended = control_repository.set_workspace_lifecycle(
        "alpha",
        "suspended",
        suspension_reason="governed test",
        updated_by_user_id=1,
    )

    assert suspended.suspended is True
    assert suspended.suspension_reason == "governed test"

    restarted_workspace_repository, restarted_control_repository = (
        _repositories(engine)
    )
    assert (
        restarted_control_repository.get_quota(
            "alpha"
        ).max_events
        == 7
    )

    with pytest.raises(WorkspaceInactiveError):
        restarted_workspace_repository.require_workspace(
            "alpha",
            require_active=True,
        )


def test_metrics_and_ingestion_are_explicitly_workspace_scoped(
    monkeypatch,
):
    engine = _isolated_engine()
    _create_control_schema(engine)
    _seed_account(engine)
    workspace_repository, control_repository = (
        _repositories(engine)
    )
    workspace_repository.create_workspace(
        workspace_id="alpha",
        name="Alpha Workspace",
        created_by_user_id=1,
        owner_user_id=1,
    )
    workspace_repository.create_workspace(
        workspace_id="beta",
        name="Beta Workspace",
        created_by_user_id=1,
        owner_user_id=1,
    )

    monkeypatch.setattr(
        event_ingestion,
        "INGESTED_EVENTS",
        [],
    )
    monkeypatch.setattr(
        event_ingestion,
        "route_memory_update",
        lambda payload: None,
    )

    alpha_event = event_ingestion.ingest_external_event(
        "slack",
        {
            "text": "alpha-only",
        },
        "alpha",
        control_repository,
    )
    beta_event = event_ingestion.ingest_external_event(
        "teams",
        {
            "text": "beta-only",
        },
        "beta",
        control_repository,
    )

    assert alpha_event["workspace"] == "alpha"
    assert beta_event["workspace"] == "beta"
    assert [
        event["workspace"]
        for event in event_ingestion.get_ingested_events(
            "alpha"
        )
    ] == ["alpha"]

    metrics = workspace_metrics(
        "alpha",
        repository=workspace_repository,
        events=event_ingestion.INGESTED_EVENTS,
    )
    assert set(metrics) == {"alpha"}
    assert metrics["alpha"]["events"] == 1


def test_workspace_control_migration_backfills_and_is_idempotent():
    engine = _isolated_engine()
    User.__table__.create(
        engine,
        checkfirst=True,
    )
    Workspace.__table__.create(
        engine,
        checkfirst=True,
    )

    with engine.begin() as connection:
        now = datetime.now(timezone.utc)
        connection.execute(
            insert(Workspace.__table__).values(
                id="alpha",
                name="Alpha Workspace",
                status="active",
                created_by_user_id=None,
                created_at=now,
                updated_at=now,
            )
        )
        apply_workspace_control(connection)
        validate_workspace_control(connection)
        apply_workspace_control(connection)
        validate_workspace_control(connection)

        controls = connection.execute(
            select(
                WorkspaceControl.__table__.c.workspace_id
            )
        ).scalars().all()

    assert controls == ["alpha"]


def test_control_plane_reads_require_governed_admin_permission():
    for path in (
        "/workspaces",
        "/workspace/admin",
        "/workspace/quotas",
        "/workspace/quotas/alpha",
        "/connectors",
        "/connectors/health",
    ):
        assert required_permission_for_route(
            "GET",
            path,
        ) == MANAGE_USERS


def test_legacy_json_and_process_state_are_not_runtime_authorities():
    registry_source = (
        ROOT
        / "app/services/workspace/registry.py"
    ).read_text(encoding="utf-8")
    admin_source = (
        ROOT
        / "app/services/workspace/admin.py"
    ).read_text(encoding="utf-8")
    quota_source = (
        ROOT
        / "app/services/workspace/quotas.py"
    ).read_text(encoding="utf-8")
    ingestion_source = (
        ROOT
        / "app/services/connectors/event_ingestion.py"
    ).read_text(encoding="utf-8")

    assert "workspace_store" not in registry_source
    assert "workspace_admin_state =" not in admin_source
    assert "workspace_quotas =" not in quota_source
    assert "get_workspace()" not in ingestion_source
