from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import (
    MetaData,
    Table,
    func,
    inspect,
    insert,
    select,
    text,
)
from sqlalchemy.engine import Connection

from app.db.migrations.runner import DatabaseMigration
from app.db.models.audit_record import AuditRecord


MIGRATION_ID = (
    "20260819_004_cap_004_unified_audit"
)

AUDIT_TABLE_NAME = "enterprise_audit_record"

_SQLITE_UPDATE_TRIGGER = (
    "trg_enterprise_audit_no_update"
)
_SQLITE_DELETE_TRIGGER = (
    "trg_enterprise_audit_no_delete"
)
_POSTGRES_TRIGGER = (
    "trg_enterprise_audit_append_only"
)
_POSTGRES_FUNCTION = (
    "cgms_prevent_enterprise_audit_mutation"
)

_MIGRATION_SIGNATURE = """
CAP-004 unified persistent enterprise audit v1
append-only enterprise_audit_record table
security domain-event explainability governance categories
nullable global or required valid workspace context
actor source subject outcome and correlation evidence
legacy security_log backfill with deterministic origin identity
workspace category action occurrence and origin indexes
SQLite and PostgreSQL update and delete rejection
"""

MIGRATION_CHECKSUM = sha256(
    _MIGRATION_SIGNATURE.encode(
        "utf-8"
    )
).hexdigest()


class UnifiedAuditMigrationError(RuntimeError):
    """Raised when the unified audit schema is invalid."""


def _table_names(
    connection: Connection,
) -> set[str]:
    return set(
        inspect(connection).get_table_names()
    )


def _legacy_details(
    value: object,
) -> dict[str, object]:
    if not isinstance(value, str) or not value:
        return {
            "legacy_details": value,
        }

    try:
        decoded = json.loads(value)
    except (
        TypeError,
        ValueError,
    ):
        return {
            "legacy_details": value,
        }

    return {
        "legacy_details": decoded,
    }


def _backfill_security_log(
    connection: Connection,
) -> None:
    if "security_log" not in _table_names(
        connection
    ):
        return

    metadata = MetaData()
    security_log = Table(
        "security_log",
        metadata,
        autoload_with=connection,
    )
    audit_table = AuditRecord.__table__

    workspace_ids = set(
        connection.execute(
            text(
                "SELECT id FROM workspace"
            )
        ).scalars().all()
    )

    rows = connection.execute(
        select(security_log).order_by(
            security_log.c.id
        )
    ).mappings().all()

    now = datetime.now(timezone.utc)

    for row in rows:
        origin_id = (
            "legacy.security_log:"
            f"{row['id']}"
        )

        existing = connection.execute(
            select(
                audit_table.c.id
            ).where(
                audit_table.c.origin_id
                == origin_id
            )
        ).first()

        if existing is not None:
            continue

        candidate_workspace_id = (
            row.get("workspace_id")
            if "workspace_id" in row
            else None
        )
        workspace_id = (
            str(candidate_workspace_id)
            if candidate_workspace_id
            in workspace_ids
            else None
        )
        details = _legacy_details(
            row.get("details")
        )

        if (
            candidate_workspace_id is not None
            and workspace_id is None
        ):
            details[
                "legacy_workspace_id"
            ] = str(
                candidate_workspace_id
            )
        occurred_at = (
            row.get("created_at")
            or now
        )

        connection.execute(
            insert(audit_table).values(
                record_id=str(
                    uuid5(
                        NAMESPACE_URL,
                        origin_id,
                    )
                ),
                origin_id=origin_id,
                category="security",
                action=(
                    str(
                        row.get("action")
                        or "legacy.security_event"
                    )[:160]
                ),
                source="legacy.security_log",
                workspace_id=workspace_id,
                actor_id=str(
                    row.get("user_id")
                ),
                subject_type="security_log",
                subject_id=str(
                    row.get("id")
                ),
                outcome="recorded",
                correlation_id=None,
                causation_id=None,
                details=details,
                occurred_at=occurred_at,
                stored_at=now,
            )
        )


def _install_append_only_controls(
    connection: Connection,
) -> None:
    dialect = connection.dialect.name

    if dialect == "sqlite":
        connection.exec_driver_sql(
            f"""
            CREATE TRIGGER IF NOT EXISTS {_SQLITE_UPDATE_TRIGGER}
            BEFORE UPDATE ON {AUDIT_TABLE_NAME}
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'enterprise audit records are append-only'
                );
            END
            """
        )
        connection.exec_driver_sql(
            f"""
            CREATE TRIGGER IF NOT EXISTS {_SQLITE_DELETE_TRIGGER}
            BEFORE DELETE ON {AUDIT_TABLE_NAME}
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'enterprise audit records are append-only'
                );
            END
            """
        )
        return

    if dialect == "postgresql":
        connection.exec_driver_sql(
            f"""
            CREATE OR REPLACE FUNCTION {_POSTGRES_FUNCTION}()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RAISE EXCEPTION
                    'enterprise audit records are append-only';
            END;
            $$
            """
        )
        connection.exec_driver_sql(
            f"DROP TRIGGER IF EXISTS {_POSTGRES_TRIGGER} "
            f"ON {AUDIT_TABLE_NAME}"
        )
        connection.exec_driver_sql(
            f"""
            CREATE TRIGGER {_POSTGRES_TRIGGER}
            BEFORE UPDATE OR DELETE ON {AUDIT_TABLE_NAME}
            FOR EACH ROW
            EXECUTE FUNCTION {_POSTGRES_FUNCTION}()
            """
        )
        return

    raise UnifiedAuditMigrationError(
        "Unified audit append-only enforcement does not support "
        f"the {dialect} database dialect."
    )


def apply_unified_audit(
    connection: Connection,
) -> None:
    if "workspace" not in _table_names(
        connection
    ):
        raise UnifiedAuditMigrationError(
            "The persistent workspace table must exist before "
            "the unified audit store is created."
        )

    AuditRecord.__table__.create(
        bind=connection,
        checkfirst=True,
    )
    _backfill_security_log(
        connection
    )
    _install_append_only_controls(
        connection
    )


def _trigger_names(
    connection: Connection,
) -> set[str]:
    if connection.dialect.name == "sqlite":
        return set(
            connection.execute(
                text(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'trigger'
                      AND tbl_name = :table_name
                    """
                ),
                {
                    "table_name": AUDIT_TABLE_NAME,
                },
            ).scalars().all()
        )

    if connection.dialect.name == "postgresql":
        return set(
            connection.execute(
                text(
                    """
                    SELECT trigger_name
                    FROM information_schema.triggers
                    WHERE event_object_table = :table_name
                    """
                ),
                {
                    "table_name": AUDIT_TABLE_NAME,
                },
            ).scalars().all()
        )

    return set()


def validate_unified_audit(
    connection: Connection,
) -> None:
    if AUDIT_TABLE_NAME not in _table_names(
        connection
    ):
        raise UnifiedAuditMigrationError(
            "The unified audit table is missing."
        )

    inspector = inspect(connection)
    columns = {
        str(column["name"]): column
        for column in inspector.get_columns(
            AUDIT_TABLE_NAME
        )
    }
    required_columns = {
        "id",
        "record_id",
        "origin_id",
        "category",
        "action",
        "source",
        "workspace_id",
        "actor_id",
        "subject_type",
        "subject_id",
        "outcome",
        "correlation_id",
        "causation_id",
        "details",
        "occurred_at",
        "stored_at",
    }
    missing = required_columns - set(
        columns
    )

    if missing:
        raise UnifiedAuditMigrationError(
            "Unified audit columns are missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    required_not_null = {
        "record_id",
        "category",
        "action",
        "source",
        "outcome",
        "details",
        "occurred_at",
        "stored_at",
    }
    nullable_required = {
        column_name
        for column_name in required_not_null
        if bool(
            columns[column_name].get(
                "nullable",
                True,
            )
        )
    }

    if nullable_required:
        raise UnifiedAuditMigrationError(
            "Required unified audit columns remain nullable: "
            + ", ".join(
                sorted(nullable_required)
            )
        )

    indexes = inspector.get_indexes(
        AUDIT_TABLE_NAME
    )
    indexed_column_sets = {
        tuple(
            str(column)
            for column in index.get(
                "column_names",
                [],
            )
            if column is not None
        )
        for index in indexes
    }
    required_indexes = {
        ("record_id",),
        ("origin_id",),
        ("category",),
        ("action",),
        ("workspace_id",),
        ("actor_id",),
        ("correlation_id",),
        ("occurred_at",),
        ("stored_at",),
    }
    missing_indexes = (
        required_indexes
        - indexed_column_sets
    )

    if missing_indexes:
        raise UnifiedAuditMigrationError(
            "Unified audit indexes are missing: "
            + ", ".join(
                index_columns[0]
                for index_columns in sorted(
                    missing_indexes
                )
            )
        )

    unique_column_sets = {
        tuple(
            str(column)
            for column in constraint.get(
                "column_names",
                [],
            )
        )
        for constraint in inspector.get_unique_constraints(
            AUDIT_TABLE_NAME
        )
    }
    unique_column_sets.update(
        tuple(
            str(column)
            for column in index.get(
                "column_names",
                [],
            )
            if column is not None
        )
        for index in indexes
        if bool(index.get("unique"))
    )

    if not {
        ("record_id",),
        ("origin_id",),
    }.issubset(
        unique_column_sets
    ):
        raise UnifiedAuditMigrationError(
            "Unified audit identity constraints are missing."
        )

    foreign_keys = inspector.get_foreign_keys(
        AUDIT_TABLE_NAME
    )
    workspace_foreign_key = any(
        foreign_key.get("constrained_columns")
        == ["workspace_id"]
        and foreign_key.get("referred_table")
        == "workspace"
        for foreign_key in foreign_keys
    )

    if not workspace_foreign_key:
        raise UnifiedAuditMigrationError(
            "The unified audit workspace foreign key is missing."
        )

    invalid_required = connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM {AUDIT_TABLE_NAME}
            WHERE TRIM(record_id) = ''
               OR TRIM(category) = ''
               OR TRIM(action) = ''
               OR TRIM(source) = ''
               OR details IS NULL
               OR occurred_at IS NULL
               OR stored_at IS NULL
            """
        )
    ).scalar_one()

    if int(invalid_required) != 0:
        raise UnifiedAuditMigrationError(
            "Invalid required unified audit evidence exists."
        )

    invalid_categories = connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM {AUDIT_TABLE_NAME}
            WHERE category NOT IN (
                'security',
                'domain_event',
                'explainability',
                'governance'
            )
            """
        )
    ).scalar_one()

    if int(invalid_categories) != 0:
        raise UnifiedAuditMigrationError(
            "Unsupported unified audit categories exist."
        )

    orphaned_workspaces = connection.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM {AUDIT_TABLE_NAME} AS audit_record
            LEFT JOIN workspace AS workspace_record
              ON workspace_record.id = audit_record.workspace_id
            WHERE audit_record.workspace_id IS NOT NULL
              AND workspace_record.id IS NULL
            """
        )
    ).scalar_one()

    if int(orphaned_workspaces) != 0:
        raise UnifiedAuditMigrationError(
            "Orphaned unified audit workspace evidence exists."
        )

    if "security_log" in _table_names(connection):
        legacy_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM security_log"
            )
        ).scalar_one()
        backfilled_count = connection.execute(
            select(
                func.count(AuditRecord.__table__.c.id)
            ).where(
                AuditRecord.__table__.c.origin_id.like(
                    "legacy.security_log:%"
                )
            )
        ).scalar_one()

        if int(backfilled_count) != int(legacy_count):
            raise UnifiedAuditMigrationError(
                "Legacy security audit backfill is incomplete."
            )

    trigger_names = _trigger_names(
        connection
    )

    if connection.dialect.name == "sqlite":
        expected = {
            _SQLITE_UPDATE_TRIGGER,
            _SQLITE_DELETE_TRIGGER,
        }
    elif connection.dialect.name == "postgresql":
        expected = {
            _POSTGRES_TRIGGER,
        }
    else:
        expected = set()

    if not expected.issubset(
        trigger_names
    ):
        raise UnifiedAuditMigrationError(
            "Unified audit append-only controls are missing."
        )


CAP_004_UNIFIED_AUDIT = DatabaseMigration(
    migration_id=MIGRATION_ID,
    checksum=MIGRATION_CHECKSUM,
    apply=apply_unified_audit,
    validate=validate_unified_audit,
)
