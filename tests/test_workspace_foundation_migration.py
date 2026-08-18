from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine

from app.db.migrations import (
    MigrationStateError,
    run_database_migrations,
)
from app.db.migrations.pwi_001_tenant_persistence import (
    MIGRATION_ID as TENANT_PERSISTENCE_MIGRATION_ID,
    TENANT_SCOPED_TABLES,
)
from app.db.migrations.pwi_001_workspace_foundation import (
    MIGRATION_ID as WORKSPACE_FOUNDATION_MIGRATION_ID,
)
from app.db.migrations.cap_003_workspace_control import (
    MIGRATION_ID as CAP_003_CONTROL_MIGRATION_ID,
)
from app.db.migrations.runner import (
    _default_migrations,
)


def build_legacy_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE "user" (
                id BIGINT PRIMARY KEY,
                email VARCHAR NOT NULL
            )
            """
        )

        connection.exec_driver_sql(
            """
            CREATE TABLE browser_session (
                id INTEGER PRIMARY KEY,
                token_id VARCHAR NOT NULL,
                user_id BIGINT NOT NULL
            )
            """
        )

        for table_name in TENANT_SCOPED_TABLES:
            quoted_table = f'"{table_name}"'

            if table_name == "memory":
                connection.exec_driver_sql(
                    f"""
                    CREATE TABLE {quoted_table} (
                        id INTEGER PRIMARY KEY,
                        summary VARCHAR NOT NULL
                    )
                    """
                )
                continue

            connection.exec_driver_sql(
                f"""
                CREATE TABLE {quoted_table} (
                    id INTEGER PRIMARY KEY,
                    payload VARCHAR
                )
                """
            )

        connection.exec_driver_sql(
            """
            CREATE TABLE security_log (
                id INTEGER PRIMARY KEY,
                user_id BIGINT NOT NULL,
                action VARCHAR NOT NULL
            )
            """
        )

        connection.exec_driver_sql(
            """
            INSERT INTO "user" (id, email)
            VALUES
                (4, 'admin@example.test'),
                (5, 'operator@example.test')
            """
        )

        connection.exec_driver_sql(
            """
            INSERT INTO browser_session (
                id,
                token_id,
                user_id
            )
            VALUES
                (1, 'session-one', 4),
                (2, 'session-two', 5)
            """
        )

        connection.exec_driver_sql(
            """
            INSERT INTO memory (
                id,
                summary
            )
            VALUES
                (1, 'Legacy memory')
            """
        )

        connection.exec_driver_sql(
            """
            INSERT INTO security_log (
                id,
                user_id,
                action
            )
            VALUES
                (1, 4, 'legacy_login')
            """
        )

    return engine


def test_default_migration_inventory_is_ordered():
    migration_ids = tuple(
        migration.migration_id
        for migration in _default_migrations()
    )

    assert migration_ids == (
        WORKSPACE_FOUNDATION_MIGRATION_ID,
        TENANT_PERSISTENCE_MIGRATION_ID,
        CAP_003_CONTROL_MIGRATION_ID,
    )


def test_foundation_migration_seeds_and_backfills():
    engine = build_legacy_engine()

    try:
        result = run_database_migrations(
            engine
        )

        assert result.applied_migrations == (
            WORKSPACE_FOUNDATION_MIGRATION_ID,
            TENANT_PERSISTENCE_MIGRATION_ID,
            CAP_003_CONTROL_MIGRATION_ID,
        )

        inspector = inspect(
            engine
        )

        tables = set(
            inspector.get_table_names()
        )

        assert {
            "schema_migration",
            "workspace",
            "workspace_membership",
            "workspace_control",
        }.issubset(
            tables
        )

        assert "workspace_id" in {
            column["name"]
            for column in inspector.get_columns(
                "memory"
            )
        }

        assert "workspace_id" in {
            column["name"]
            for column in inspector.get_columns(
                "browser_session"
            )
        }

        assert "workspace_id" in {
            column["name"]
            for column in inspector.get_columns(
                "security_log"
            )
        }

        with engine.connect() as connection:
            workspace = connection.execute(
                text(
                    """
                    SELECT id, name, status
                    FROM workspace
                    WHERE id = 'default'
                    """
                )
            ).one()

            assert tuple(workspace) == (
                "default",
                "Default Workspace",
                "active",
            )

            memberships = connection.execute(
                text(
                    """
                    SELECT user_id
                    FROM workspace_membership
                    WHERE workspace_id = 'default'
                      AND status = 'active'
                      AND is_default = 1
                    ORDER BY user_id
                    """
                )
            ).scalars().all()

            assert memberships == [
                4,
                5,
            ]

            memory_workspace = (
                connection.execute(
                    text(
                        """
                        SELECT workspace_id
                        FROM memory
                        WHERE id = 1
                        """
                    )
                ).scalar_one()
            )

            assert memory_workspace == "default"

            session_workspaces = (
                connection.execute(
                    text(
                        """
                        SELECT workspace_id
                        FROM browser_session
                        ORDER BY id
                        """
                    )
                ).scalars().all()
            )

            assert session_workspaces == [
                "default",
                "default",
            ]

            security_workspace = (
                connection.execute(
                    text(
                        """
                        SELECT workspace_id
                        FROM security_log
                        WHERE id = 1
                        """
                    )
                ).scalar_one()
            )

            assert security_workspace is None

    finally:
        engine.dispose()


def test_foundation_migration_is_idempotent():
    engine = build_legacy_engine()

    try:
        first = run_database_migrations(
            engine
        )

        second = run_database_migrations(
            engine
        )

        assert first.applied_migrations == (
            WORKSPACE_FOUNDATION_MIGRATION_ID,
            TENANT_PERSISTENCE_MIGRATION_ID,
            CAP_003_CONTROL_MIGRATION_ID,
        )

        assert second.applied_migrations == ()
        assert second.skipped_migrations == (
            WORKSPACE_FOUNDATION_MIGRATION_ID,
            TENANT_PERSISTENCE_MIGRATION_ID,
            CAP_003_CONTROL_MIGRATION_ID,
        )

        with engine.connect() as connection:
            ledger_rows = connection.execute(
                text(
                    """
                    SELECT migration_id
                    FROM schema_migration
                    ORDER BY applied_at, migration_id
                    """
                )
            ).scalars().all()

            assert set(ledger_rows) == {
                WORKSPACE_FOUNDATION_MIGRATION_ID,
                TENANT_PERSISTENCE_MIGRATION_ID,
                CAP_003_CONTROL_MIGRATION_ID,
            }
            assert len(ledger_rows) == 3

    finally:
        engine.dispose()


def test_migration_checksum_mismatch_fails_closed():
    engine = build_legacy_engine()

    try:
        run_database_migrations(
            engine
        )

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE schema_migration
                    SET checksum = :checksum
                    WHERE migration_id = :migration_id
                    """
                ),
                {
                    "checksum": "0" * 64,
                    "migration_id":
                        WORKSPACE_FOUNDATION_MIGRATION_ID,
                },
            )

        with pytest.raises(
            MigrationStateError
        ):
            run_database_migrations(
                engine
            )

    finally:
        engine.dispose()


def test_transitional_default_scopes_new_rows():
    engine = build_legacy_engine()

    try:
        run_database_migrations(
            engine
        )

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO memory (
                        id,
                        summary
                    )
                    VALUES (
                        2,
                        'Post-migration memory'
                    )
                    """
                )
            )

        with engine.connect() as connection:
            workspace_id = connection.execute(
                text(
                    """
                    SELECT workspace_id
                    FROM memory
                    WHERE id = 2
                    """
                )
            ).scalar_one()

            assert workspace_id == "default"

    finally:
        engine.dispose()
