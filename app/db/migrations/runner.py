from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    insert,
    select,
)
from sqlalchemy.engine import Connection, Engine


class DatabaseMigrationError(RuntimeError):
    """Base error for governed CGMS database migrations."""


class MigrationStateError(DatabaseMigrationError):
    """Raised when applied migration state is inconsistent."""


@dataclass(frozen=True)
class DatabaseMigration:
    migration_id: str
    checksum: str
    apply: Callable[[Connection], None]
    validate: Callable[[Connection], None]


@dataclass(frozen=True)
class MigrationRunResult:
    applied_migrations: tuple[str, ...]
    skipped_migrations: tuple[str, ...]


_LEDGER_METADATA = MetaData()

SCHEMA_MIGRATION_TABLE = Table(
    "schema_migration",
    _LEDGER_METADATA,
    Column(
        "migration_id",
        String(128),
        primary_key=True,
    ),
    Column(
        "checksum",
        String(64),
        nullable=False,
    ),
    Column(
        "applied_at",
        DateTime(timezone=True),
        nullable=False,
    ),
)


def _validate_migration_inventory(
    migrations: Iterable[DatabaseMigration],
) -> tuple[DatabaseMigration, ...]:
    resolved = tuple(migrations)

    migration_ids = [
        migration.migration_id
        for migration in resolved
    ]

    if len(migration_ids) != len(set(migration_ids)):
        raise MigrationStateError(
            "Database migration identifiers must be unique."
        )

    for migration in resolved:
        if not migration.migration_id.strip():
            raise MigrationStateError(
                "Database migration identifier is empty."
            )

        if len(migration.checksum) != 64:
            raise MigrationStateError(
                "Database migration checksum is invalid."
            )

    return resolved


def _default_migrations() -> tuple[DatabaseMigration, ...]:
    from app.db.migrations.pwi_001_workspace_foundation import (
        PWI_001_WORKSPACE_FOUNDATION,
    )
    from app.db.migrations.pwi_001_tenant_persistence import (
        PWI_001_TENANT_PERSISTENCE,
    )
    from app.db.migrations.cap_003_workspace_control import (
        CAP_003_WORKSPACE_CONTROL,
    )
    from app.db.migrations.cap_004_unified_audit import (
        CAP_004_UNIFIED_AUDIT,
    )

    return (
        PWI_001_WORKSPACE_FOUNDATION,
        PWI_001_TENANT_PERSISTENCE,
        CAP_003_WORKSPACE_CONTROL,
        CAP_004_UNIFIED_AUDIT,
    )


def run_database_migrations(
    engine: Engine,
    *,
    migrations: Iterable[DatabaseMigration] | None = None,
) -> MigrationRunResult:
    resolved_migrations = _validate_migration_inventory(
        (
            migrations
            if migrations is not None
            else _default_migrations()
        )
    )

    applied_now: list[str] = []
    skipped: list[str] = []

    with engine.begin() as connection:
        SCHEMA_MIGRATION_TABLE.create(
            bind=connection,
            checkfirst=True,
        )

        applied_rows = connection.execute(
            select(
                SCHEMA_MIGRATION_TABLE.c.migration_id,
                SCHEMA_MIGRATION_TABLE.c.checksum,
            )
        ).all()

        applied = {
            str(row.migration_id):
                str(row.checksum)
            for row in applied_rows
        }

        for migration in resolved_migrations:
            existing_checksum = applied.get(
                migration.migration_id
            )

            if existing_checksum is not None:
                if existing_checksum != migration.checksum:
                    raise MigrationStateError(
                        "Applied migration checksum does not "
                        "match the current migration definition: "
                        f"{migration.migration_id}"
                    )

                migration.validate(connection)
                skipped.append(
                    migration.migration_id
                )
                continue

            migration.apply(connection)
            migration.validate(connection)

            connection.execute(
                insert(
                    SCHEMA_MIGRATION_TABLE
                ).values(
                    migration_id=(
                        migration.migration_id
                    ),
                    checksum=migration.checksum,
                    applied_at=datetime.now(
                        timezone.utc
                    ),
                )
            )

            applied_now.append(
                migration.migration_id
            )

    return MigrationRunResult(
        applied_migrations=tuple(applied_now),
        skipped_migrations=tuple(skipped),
    )
