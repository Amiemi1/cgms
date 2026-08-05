from __future__ import annotations

from hashlib import sha256

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from app.db.migrations.pwi_001_workspace_foundation import (
    DEFAULT_WORKSPACE_ID,
)
from app.db.migrations.runner import DatabaseMigration


MIGRATION_ID = "20260802_002_pwi_tenant_persistence"

TENANT_SCOPED_TABLES = (
    "candidate_memory",
    "decision_lineage",
    "goal",
    "insight",
    "learning",
    "learning_log",
    "memory",
    "memory_access",
    "memory_relationship",
    "memoryscore",
    "message",
)

_MIGRATION_SIGNATURE = """
PWI-001 tenant persistence contract v1
eleven required tenant-scoped persistence tables
legacy null and blank ownership backfill
workspace ownership index verification
PostgreSQL not-null check and foreign-key enforcement
SQLite insert and update ownership enforcement triggers
orphaned workspace ownership rejection
ordered checksum-governed migration contract
"""

MIGRATION_CHECKSUM = sha256(
    _MIGRATION_SIGNATURE.encode("utf-8")
).hexdigest()


class TenantPersistenceMigrationError(RuntimeError):
    """Raised when tenant persistence invariants are invalid."""


def _quote_identifier(
    connection: Connection,
    identifier: str,
) -> str:
    return (
        connection.dialect
        .identifier_preparer
        .quote(identifier)
    )


def _table_names(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names())


def _column_map(
    connection: Connection,
    table_name: str,
) -> dict[str, dict[str, object]]:
    return {
        str(column["name"]): column
        for column in inspect(connection).get_columns(table_name)
    }


def _index_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(index["name"])
        for index in inspect(connection).get_indexes(table_name)
        if index.get("name")
    }


def _foreign_keys(
    connection: Connection,
    table_name: str,
) -> list[dict[str, object]]:
    return list(inspect(connection).get_foreign_keys(table_name))


def _require_foundation(connection: Connection) -> None:
    tables = _table_names(connection)
    required = {"workspace", *TENANT_SCOPED_TABLES}
    missing = sorted(required - tables)

    if missing:
        raise TenantPersistenceMigrationError(
            "Tenant persistence tables are missing: "
            + ", ".join(missing)
        )

    default_status = connection.execute(
        text(
            """
            SELECT status
            FROM workspace
            WHERE id = :workspace_id
            """
        ),
        {"workspace_id": DEFAULT_WORKSPACE_ID},
    ).scalar_one_or_none()

    if default_status != "active":
        raise TenantPersistenceMigrationError(
            "The governed default workspace is missing or inactive."
        )


def _backfill_workspace(
    connection: Connection,
    table_name: str,
) -> None:
    columns = _column_map(connection, table_name)

    if "workspace_id" not in columns:
        raise TenantPersistenceMigrationError(
            "Required workspace column is missing "
            f"from {table_name}."
        )

    quoted_table = _quote_identifier(connection, table_name)

    connection.execute(
        text(
            f"UPDATE {quoted_table} "
            "SET workspace_id = :workspace_id "
            "WHERE workspace_id IS NULL "
            "OR TRIM(workspace_id) = ''"
        ),
        {"workspace_id": DEFAULT_WORKSPACE_ID},
    )


def _create_workspace_index(
    connection: Connection,
    table_name: str,
) -> None:
    index_name = f"ix_{table_name}_workspace_id"

    if index_name in _index_names(connection, table_name):
        return

    quoted_table = _quote_identifier(connection, table_name)
    quoted_index = _quote_identifier(connection, index_name)

    connection.execute(
        text(
            f"CREATE INDEX {quoted_index} "
            f"ON {quoted_table} (workspace_id)"
        )
    )


def _postgres_constraint_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            text(
                """
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).all()
    }


def _enforce_postgresql(
    connection: Connection,
    table_name: str,
) -> None:
    quoted_table = _quote_identifier(connection, table_name)
    constraint_names = _postgres_constraint_names(
        connection,
        table_name,
    )

    check_name = f"ck_{table_name}_workspace_required"
    foreign_key_name = (
        f"fk_{table_name}_workspace_id_workspace"
    )

    if check_name not in constraint_names:
        quoted_check = _quote_identifier(
            connection,
            check_name,
        )
        connection.execute(
            text(
                f"ALTER TABLE {quoted_table} "
                f"ADD CONSTRAINT {quoted_check} "
                "CHECK (BTRIM(workspace_id) <> '')"
            )
        )

    existing_workspace_fk = any(
        list(foreign_key.get("constrained_columns", []))
        == ["workspace_id"]
        and foreign_key.get("referred_table") == "workspace"
        for foreign_key in _foreign_keys(connection, table_name)
    )

    if not existing_workspace_fk:
        quoted_foreign_key = _quote_identifier(
            connection,
            foreign_key_name,
        )
        connection.execute(
            text(
                f"ALTER TABLE {quoted_table} "
                f"ADD CONSTRAINT {quoted_foreign_key} "
                "FOREIGN KEY (workspace_id) "
                "REFERENCES workspace(id)"
            )
        )

    connection.execute(
        text(
            f"ALTER TABLE {quoted_table} "
            "ALTER COLUMN workspace_id SET NOT NULL"
        )
    )


def _sqlite_trigger_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            text(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'trigger'
                  AND tbl_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).all()
    }


def _enforce_sqlite(
    connection: Connection,
    table_name: str,
) -> None:
    quoted_table = _quote_identifier(connection, table_name)
    trigger_names = _sqlite_trigger_names(
        connection,
        table_name,
    )

    definitions = (
        (
            f"trg_{table_name}_workspace_insert",
            "INSERT",
        ),
        (
            f"trg_{table_name}_workspace_update",
            "UPDATE OF workspace_id",
        ),
    )

    for trigger_name, operation in definitions:
        if trigger_name in trigger_names:
            continue

        quoted_trigger = _quote_identifier(
            connection,
            trigger_name,
        )

        connection.execute(
            text(
                f"""
                CREATE TRIGGER {quoted_trigger}
                BEFORE {operation} ON {quoted_table}
                FOR EACH ROW
                WHEN (
                    NEW.workspace_id IS NULL
                    OR TRIM(NEW.workspace_id) = ''
                    OR NOT EXISTS (
                        SELECT 1
                        FROM workspace
                        WHERE id = NEW.workspace_id
                    )
                )
                BEGIN
                    SELECT RAISE(
                        ABORT,
                        'invalid tenant workspace ownership'
                    );
                END
                """
            )
        )


def _enforce_workspace_ownership(
    connection: Connection,
    table_name: str,
) -> None:
    dialect = connection.dialect.name

    if dialect == "postgresql":
        _enforce_postgresql(connection, table_name)
        return

    if dialect == "sqlite":
        _enforce_sqlite(connection, table_name)
        return

    columns = _column_map(connection, table_name)

    if bool(columns["workspace_id"].get("nullable", True)):
        raise TenantPersistenceMigrationError(
            "The database dialect cannot enforce "
            "required tenant ownership safely: "
            f"{dialect}"
        )


def apply_tenant_persistence(
    connection: Connection,
) -> None:
    _require_foundation(connection)

    for table_name in TENANT_SCOPED_TABLES:
        _backfill_workspace(connection, table_name)
        _create_workspace_index(connection, table_name)

    for table_name in TENANT_SCOPED_TABLES:
        _enforce_workspace_ownership(connection, table_name)


def _validate_table(
    connection: Connection,
    table_name: str,
) -> None:
    columns = _column_map(connection, table_name)

    if "workspace_id" not in columns:
        raise TenantPersistenceMigrationError(
            "Required workspace column is missing "
            f"from {table_name}."
        )

    quoted_table = _quote_identifier(connection, table_name)

    unscoped_count = int(
        connection.execute(
            text(
                f"SELECT COUNT(*) FROM {quoted_table} "
                "WHERE workspace_id IS NULL "
                "OR TRIM(workspace_id) = ''"
            )
        ).scalar_one()
    )

    if unscoped_count != 0:
        raise TenantPersistenceMigrationError(
            "Unscoped tenant records remain in "
            f"{table_name}."
        )

    orphan_count = int(
        connection.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM {quoted_table} AS tenant_record "
                "LEFT JOIN workspace AS workspace_record "
                "ON workspace_record.id "
                "= tenant_record.workspace_id "
                "WHERE workspace_record.id IS NULL"
            )
        ).scalar_one()
    )

    if orphan_count != 0:
        raise TenantPersistenceMigrationError(
            "Orphaned workspace ownership remains in "
            f"{table_name}."
        )

    expected_index = f"ix_{table_name}_workspace_id"

    if expected_index not in _index_names(
        connection,
        table_name,
    ):
        raise TenantPersistenceMigrationError(
            "Required workspace index is missing from "
            f"{table_name}."
        )

    dialect = connection.dialect.name

    if dialect == "postgresql":
        if bool(
            columns["workspace_id"].get("nullable", True)
        ):
            raise TenantPersistenceMigrationError(
                "Tenant workspace ownership remains "
                f"nullable in {table_name}."
            )

        existing_workspace_fk = any(
            list(
                foreign_key.get(
                    "constrained_columns",
                    [],
                )
            )
            == ["workspace_id"]
            and foreign_key.get("referred_table") == "workspace"
            for foreign_key in _foreign_keys(
                connection,
                table_name,
            )
        )

        if not existing_workspace_fk:
            raise TenantPersistenceMigrationError(
                "Workspace foreign key is missing from "
                f"{table_name}."
            )

    elif dialect == "sqlite":
        trigger_names = _sqlite_trigger_names(
            connection,
            table_name,
        )
        expected_triggers = {
            f"trg_{table_name}_workspace_insert",
            f"trg_{table_name}_workspace_update",
        }

        if not expected_triggers.issubset(trigger_names):
            raise TenantPersistenceMigrationError(
                "SQLite tenant enforcement triggers "
                f"are missing from {table_name}."
            )


def validate_tenant_persistence(
    connection: Connection,
) -> None:
    _require_foundation(connection)

    for table_name in TENANT_SCOPED_TABLES:
        _validate_table(connection, table_name)


PWI_001_TENANT_PERSISTENCE = DatabaseMigration(
    migration_id=MIGRATION_ID,
    checksum=MIGRATION_CHECKSUM,
    apply=apply_tenant_persistence,
    validate=validate_tenant_persistence,
)
