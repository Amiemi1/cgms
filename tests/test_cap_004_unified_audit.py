from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select

from app.dashboard.routes.audit_console import audit_records
from app.db.migrations.cap_004_unified_audit import (
    apply_unified_audit,
    validate_unified_audit,
)
from app.db.models.audit_record import AuditRecord
from app.db.models.security_models import SecurityLog
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.explainability.audit_store import (
    store_audit_record,
)
from app.services.persistence.audit_store import (
    AuditValidationError,
    DOMAIN_EVENT_AUDIT,
    EXPLAINABILITY_AUDIT,
    GOVERNANCE_AUDIT,
    SECURITY_AUDIT,
    PersistentAuditStore,
    add_audit_record,
)
from app.services.security.rbac_policy import (
    get_permissions,
)
from app.services.security.audit_service import (
    get_recent_audit,
    record_audit,
)
from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]


def _isolated_engine():
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
    SecurityLog.__table__.create(
        engine,
        checkfirst=True,
    )
    AuditRecord.__table__.create(
        engine,
        checkfirst=True,
    )

    with Session(engine) as session:
        session.add_all(
            [
                Workspace(
                    id="alpha",
                    name="Alpha Workspace",
                    status="active",
                ),
                Workspace(
                    id="beta",
                    name="Beta Workspace",
                    status="active",
                ),
            ]
        )
        session.commit()

    return engine


def _store(engine) -> PersistentAuditStore:
    return PersistentAuditStore(
        lambda: Session(engine)
    )


def test_all_audit_categories_persist_and_reads_are_workspace_scoped():
    engine = _isolated_engine()
    store = _store(engine)

    for category in (
        SECURITY_AUDIT,
        DOMAIN_EVENT_AUDIT,
        EXPLAINABILITY_AUDIT,
        GOVERNANCE_AUDIT,
    ):
        store.append(
            category=category,
            action=f"{category}.recorded",
            source="cap_004_test",
            workspace_id="alpha",
            actor_id="1001",
            details={
                "category": category,
            },
        )

    store.append(
        category=SECURITY_AUDIT,
        action="beta.security.recorded",
        source="cap_004_test",
        workspace_id="beta",
        actor_id="2001",
        details={},
    )
    store.append(
        category=SECURITY_AUDIT,
        action="global.security.recorded",
        source="cap_004_test",
        actor_id="0",
        details={},
    )

    restarted_store = _store(engine)
    alpha_records = restarted_store.list_for_workspace(
        "alpha"
    )

    assert {
        record.category
        for record in alpha_records
    } == {
        SECURITY_AUDIT,
        DOMAIN_EVENT_AUDIT,
        EXPLAINABILITY_AUDIT,
        GOVERNANCE_AUDIT,
    }
    assert {
        record.workspace_id
        for record in alpha_records
    } == {"alpha"}
    assert all(
        not record.action.startswith(
            "beta."
        )
        and not record.action.startswith(
            "global."
        )
        for record in alpha_records
    )

    alpha_with_global = (
        restarted_store.list_for_workspace(
            "alpha",
            include_global=True,
        )
    )
    assert {
        record.workspace_id
        for record in alpha_with_global
    } == {
        "alpha",
        None,
    }
    assert all(
        record.workspace_id != "beta"
        for record in alpha_with_global
    )

    engine.dispose()


def test_explainability_and_console_share_the_persistent_boundary():
    engine = _isolated_engine()
    store = _store(engine)

    store_audit_record(
        {
            "event": "runtime_state_changed",
            "decision": "monitor",
        },
        workspace_id="alpha",
        actor_id="1001",
        correlation_id="corr-alpha",
        audit_store=store,
    )
    store_audit_record(
        {
            "event": "incident",
            "decision": "escalate",
        },
        workspace_id="beta",
        actor_id="2001",
        audit_store=store,
    )

    principal = AuthenticatedPrincipal(
        user_id="1001",
        workspace_id="alpha",
        role="admin",
        permissions=get_permissions(
            "admin"
        ),
    )
    response = audit_records(
        principal=principal,
        audit_store=_store(engine),
        limit=50,
        include_global=False,
    )

    assert len(response["records"]) == 1
    assert response["records"][0][
        "workspace_id"
    ] == "alpha"
    assert response["records"][0][
        "category"
    ] == EXPLAINABILITY_AUDIT
    assert response["records"][0][
        "correlation_id"
    ] == "corr-alpha"

    operator = AuthenticatedPrincipal(
        user_id="1002",
        workspace_id="alpha",
        role="operator",
        permissions=get_permissions(
            "operator"
        ),
    )

    with pytest.raises(HTTPException) as denied:
        audit_records(
            principal=operator,
            audit_store=_store(engine),
            limit=50,
            include_global=True,
        )

    assert denied.value.status_code == 403

    engine.dispose()


def test_audit_details_fail_closed_when_not_json_serializable():
    engine = _isolated_engine()

    with pytest.raises(
        AuditValidationError
    ):
        _store(engine).append(
            category=GOVERNANCE_AUDIT,
            action="invalid.details",
            source="cap_004_test",
            workspace_id="alpha",
            details={
                "invalid": object(),
            },
        )

    with Session(engine) as session:
        assert session.exec(
            select(AuditRecord)
        ).all() == []

    engine.dispose()


def test_governance_audit_uses_the_unified_transaction_boundary():
    engine = _isolated_engine()

    with Session(engine) as session:
        record_audit(
            session,
            1001,
            "role_change",
            "Role updated to operator",
            workspace_id="alpha",
            subject_type="account_role",
            subject_id=1002,
            commit=False,
        )
        session.rollback()

    assert _store(engine).list_for_workspace(
        "alpha"
    ) == ()

    with Session(engine) as session:
        record_audit(
            session,
            1001,
            "role_change",
            "Role updated to operator",
            workspace_id="alpha",
            subject_type="account_role",
            subject_id=1002,
        )

    with Session(engine) as session:
        records = get_recent_audit(
            session,
            workspace_id="alpha",
        )

    assert len(records) == 1
    assert records[0][0] == "1001"
    assert records[0][1] == "role_change"
    assert (
        "Role updated to operator"
        in records[0][2]
    )

    engine.dispose()


def test_audit_evidence_survives_a_separate_python_process(
    tmp_path: Path,
):
    database_path = (
        tmp_path
        / "cap_004_process_restart.sqlite3"
    )
    engine = create_engine(
        f"sqlite:///{database_path}"
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
                id="alpha",
                name="Alpha Workspace",
                status="active",
            )
        )
        session.commit()

    record = _store(engine).append(
        category=DOMAIN_EVENT_AUDIT,
        action="memory.created",
        source="cap_004_process_test",
        workspace_id="alpha",
        actor_id="1001",
        details={
            "memory_id": 77,
        },
    )
    engine.dispose()

    script = """
import sys
from sqlmodel import Session, create_engine, select
from app.db.models.audit_record import AuditRecord

engine = create_engine(sys.argv[1])
with Session(engine) as session:
    record = session.exec(select(AuditRecord)).one()
    print(record.record_id)
    print(record.action)
engine.dispose()
"""
    environment = dict(
        os.environ
    )
    environment[
        "PYTHONDONTWRITEBYTECODE"
    ] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            f"sqlite:///{database_path}",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.splitlines() == [
        record.record_id,
        "memory.created",
    ]


def test_migration_backfills_security_log_and_enforces_append_only():
    engine = _isolated_engine()
    created_at = datetime(
        2026,
        8,
        19,
        8,
        0,
        tzinfo=timezone.utc,
    )

    with Session(engine) as session:
        session.add(
            SecurityLog(
                user_id=1001,
                workspace_id="alpha",
                action="browser_login_success",
                details='{"subject_key":"safe-key"}',
                created_at=created_at,
            )
        )
        session.commit()

    AuditRecord.__table__.drop(
        engine,
        checkfirst=True,
    )

    with engine.begin() as connection:
        apply_unified_audit(
            connection
        )
        validate_unified_audit(
            connection
        )
        apply_unified_audit(
            connection
        )
        validate_unified_audit(
            connection
        )

    with Session(engine) as session:
        record = session.exec(
            select(AuditRecord)
        ).one()

        assert record.origin_id == (
            "legacy.security_log:1"
        )
        assert record.workspace_id == "alpha"
        assert record.category == SECURITY_AUDIT
        assert record.details == {
            "legacy_details": {
                "subject_key": "safe-key",
            }
        }

    with Session(engine) as session:
        security_log = SecurityLog(
            user_id=1002,
            workspace_id="beta",
            action="browser_login_success",
            details='{"subject_key":"second-safe-key"}',
            created_at=created_at,
        )
        session.add(
            security_log
        )
        session.flush()
        add_audit_record(
            session,
            category=SECURITY_AUDIT,
            action=security_log.action,
            source="cap_004_test",
            workspace_id="beta",
            actor_id=1002,
            details={
                "subject_key": "second-safe-key",
            },
            origin_id=(
                "legacy.security_log:"
                f"{security_log.id}"
            ),
        )
        session.commit()

    with engine.connect() as connection:
        validate_unified_audit(
            connection
        )

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE enterprise_audit_record
                    SET action = 'tampered'
                    WHERE id = 1
                    """
                )
            )

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM enterprise_audit_record
                    WHERE id = 1
                    """
                )
            )

    engine.dispose()
