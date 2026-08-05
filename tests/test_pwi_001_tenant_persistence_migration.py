from __future__ import annotations

import pytest
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    inspect,
    text,
)
from sqlalchemy.pool import StaticPool

from app.db.migrations.pwi_001_tenant_persistence import (
    MIGRATION_CHECKSUM,
    MIGRATION_ID,
    PWI_001_TENANT_PERSISTENCE,
    TENANT_SCOPED_TABLES,
    TenantPersistenceMigrationError,
    apply_tenant_persistence,
    validate_tenant_persistence,
)


def build_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def create_legacy_schema(
    engine,
    *,
    omit_table: str | None = None,
) -> None:
    metadata = MetaData()

    workspace = Table(
        "workspace",
        metadata,
        Column("id", String(64), primary_key=True),
        Column("status", String(32), nullable=False),
    )

    for table_name in TENANT_SCOPED_TABLES:
        if table_name == omit_table:
            continue

        Table(
            table_name,
            metadata,
            Column("id", Integer, primary_key=True),
            Column(
                "workspace_id",
                String(64),
                nullable=True,
            ),
            Column(
                "payload",
                String(128),
                nullable=True,
            ),
        )

    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            insert(workspace),
            (
                {"id": "default", "status": "active"},
                {"id": "workspace-b", "status": "active"},
            ),
        )

        for table_name in TENANT_SCOPED_TABLES:
            if table_name == omit_table:
                continue

            table = metadata.tables[table_name]
            connection.execute(
                insert(table),
                (
                    {
                        "id": 1,
                        "workspace_id": None,
                        "payload": "null",
                    },
                    {
                        "id": 2,
                        "workspace_id": "",
                        "payload": "blank",
                    },
                    {
                        "id": 3,
                        "workspace_id": "workspace-b",
                        "payload": "preserved",
                    },
                ),
            )


def test_contract_identity_is_checksum_governed() -> None:
    assert MIGRATION_ID == (
        "20260802_002_pwi_tenant_persistence"
    )
    assert len(MIGRATION_CHECKSUM) == 64
    assert (
        PWI_001_TENANT_PERSISTENCE.migration_id
        == MIGRATION_ID
    )
    assert (
        PWI_001_TENANT_PERSISTENCE.checksum
        == MIGRATION_CHECKSUM
    )


def test_backfills_validates_and_is_idempotent() -> None:
    engine = build_engine()
    create_legacy_schema(engine)

    with engine.begin() as connection:
        apply_tenant_persistence(connection)
        validate_tenant_persistence(connection)
        apply_tenant_persistence(connection)
        validate_tenant_persistence(connection)

        inspector = inspect(connection)

        for table_name in TENANT_SCOPED_TABLES:
            rows = connection.execute(
                text(
                    f"""
                    SELECT id, workspace_id
                    FROM {table_name}
                    ORDER BY id
                    """
                )
            ).all()

            assert rows == [
                (1, "default"),
                (2, "default"),
                (3, "workspace-b"),
            ]

            index_names = {
                item["name"]
                for item in inspector.get_indexes(table_name)
            }
            assert (
                f"ix_{table_name}_workspace_id"
                in index_names
            )

            trigger_names = {
                row[0]
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

            assert {
                f"trg_{table_name}_workspace_insert",
                f"trg_{table_name}_workspace_update",
            }.issubset(trigger_names)


def test_enforcement_blocks_invalid_future_ownership() -> None:
    engine = build_engine()
    create_legacy_schema(engine)

    with engine.begin() as connection:
        apply_tenant_persistence(connection)
        validate_tenant_persistence(connection)

        with pytest.raises(Exception):
            connection.execute(
                text(
                    """
                    INSERT INTO memory (
                        id,
                        workspace_id,
                        payload
                    )
                    VALUES (20, NULL, 'invalid')
                    """
                )
            )

        with pytest.raises(Exception):
            connection.execute(
                text(
                    """
                    INSERT INTO memory (
                        id,
                        workspace_id,
                        payload
                    )
                    VALUES (
                        21,
                        'missing-workspace',
                        'invalid'
                    )
                    """
                )
            )


def test_missing_required_table_fails_closed() -> None:
    engine = build_engine()
    create_legacy_schema(
        engine,
        omit_table="learning_log",
    )

    with engine.begin() as connection:
        with pytest.raises(
            TenantPersistenceMigrationError,
            match="tables are missing",
        ):
            apply_tenant_persistence(connection)


def test_orphaned_ownership_fails_validation() -> None:
    engine = build_engine()
    create_legacy_schema(engine)

    with engine.begin() as connection:
        apply_tenant_persistence(connection)

        connection.execute(
            text(
                """
                DROP TRIGGER trg_memory_workspace_update
                """
            )
        )

        connection.execute(
            text(
                """
                UPDATE memory
                SET workspace_id = 'orphan'
                WHERE id = 3
                """
            )
        )

        with pytest.raises(
            TenantPersistenceMigrationError,
            match="Orphaned workspace ownership",
        ):
            validate_tenant_persistence(connection)
