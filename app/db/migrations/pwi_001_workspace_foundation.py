from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import (
    insert,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import Connection

from app.db.migrations.runner import DatabaseMigration
from app.db.models.user import User
from app.db.models.workspace import (
    Workspace,
    WorkspaceMembership,
)


MIGRATION_ID = (
    "20260728_001_pwi_workspace_foundation"
)

DEFAULT_WORKSPACE_ID = "default"

REQUIRED_SCOPED_TABLES = (
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
    "browser_session",
)

OPTIONAL_SCOPED_TABLES = (
    "security_log",
)

_MIGRATION_SIGNATURE = """
PWI-001 workspace foundation v1
workspace and workspace_membership tables
nullable transitional workspace_id expansion
default workspace and membership backfill
tenant-owned and browser-session default backfill
nullable security-log workspace context
supporting workspace indexes
"""

MIGRATION_CHECKSUM = sha256(
    _MIGRATION_SIGNATURE.encode(
        "utf-8"
    )
).hexdigest()


class WorkspaceFoundationMigrationError(
    RuntimeError
):
    """Raised when the workspace foundation is invalid."""


def _quote_identifier(
    connection: Connection,
    identifier: str,
) -> str:
    return (
        connection.dialect
        .identifier_preparer
        .quote(identifier)
    )


def _table_names(
    connection: Connection,
) -> set[str]:
    return set(
        inspect(connection).get_table_names()
    )


def _column_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(column["name"])
        for column in inspect(
            connection
        ).get_columns(
            table_name
        )
    }


def _create_foundation_tables(
    connection: Connection,
) -> None:
    tables = _table_names(
        connection
    )

    if "user" not in tables:
        raise WorkspaceFoundationMigrationError(
            "The base user table must exist before "
            "the workspace migration is applied."
        )

    Workspace.__table__.create(
        bind=connection,
        checkfirst=True,
    )

    WorkspaceMembership.__table__.create(
        bind=connection,
        checkfirst=True,
    )


def _add_workspace_column(
    connection: Connection,
    table_name: str,
    *,
    default_to_workspace: bool,
) -> None:
    if table_name not in _table_names(
        connection
    ):
        return

    if "workspace_id" in _column_names(
        connection,
        table_name,
    ):
        return

    quoted_table = _quote_identifier(
        connection,
        table_name,
    )

    default_clause = (
        " DEFAULT 'default'"
        if default_to_workspace
        else ""
    )

    connection.exec_driver_sql(
        (
            f"ALTER TABLE {quoted_table} "
            "ADD COLUMN workspace_id VARCHAR(64)"
            f"{default_clause}"
        )
    )


def _create_workspace_index(
    connection: Connection,
    table_name: str,
) -> None:
    if table_name not in _table_names(
        connection
    ):
        return

    if "workspace_id" not in _column_names(
        connection,
        table_name,
    ):
        return

    index_name = (
        f"ix_{table_name}_workspace_id"
    )

    quoted_index = _quote_identifier(
        connection,
        index_name,
    )

    quoted_table = _quote_identifier(
        connection,
        table_name,
    )

    connection.exec_driver_sql(
        (
            f"CREATE INDEX IF NOT EXISTS "
            f"{quoted_index} "
            f"ON {quoted_table} (workspace_id)"
        )
    )


def _seed_default_workspace(
    connection: Connection,
) -> None:
    workspace_table = Workspace.__table__

    existing = connection.execute(
        select(
            workspace_table.c.id
        ).where(
            workspace_table.c.id
            == DEFAULT_WORKSPACE_ID
        )
    ).first()

    if existing is not None:
        return

    now = datetime.now(
        timezone.utc
    )

    connection.execute(
        insert(
            workspace_table
        ).values(
            id=DEFAULT_WORKSPACE_ID,
            name="Default Workspace",
            status="active",
            created_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
    )


def _seed_default_memberships(
    connection: Connection,
) -> None:
    user_table = User.__table__
    membership_table = (
        WorkspaceMembership.__table__
    )

    user_ids = connection.execute(
        select(
            user_table.c.id
        ).order_by(
            user_table.c.id
        )
    ).scalars().all()

    now = datetime.now(
        timezone.utc
    )

    for user_id in user_ids:
        existing = connection.execute(
            select(
                membership_table.c.id
            ).where(
                membership_table.c.workspace_id
                == DEFAULT_WORKSPACE_ID,
                membership_table.c.user_id
                == user_id,
            )
        ).first()

        if existing is not None:
            continue

        connection.execute(
            insert(
                membership_table
            ).values(
                workspace_id=DEFAULT_WORKSPACE_ID,
                user_id=user_id,
                status="active",
                is_default=True,
                created_at=now,
                updated_at=now,
            )
        )


def _backfill_required_table(
    connection: Connection,
    table_name: str,
) -> None:
    if table_name not in _table_names(
        connection
    ):
        return

    if "workspace_id" not in _column_names(
        connection,
        table_name,
    ):
        raise WorkspaceFoundationMigrationError(
            "Workspace column is missing from "
            f"{table_name}."
        )

    quoted_table = _quote_identifier(
        connection,
        table_name,
    )

    connection.execute(
        text(
            (
                f"UPDATE {quoted_table} "
                "SET workspace_id = :workspace_id "
                "WHERE workspace_id IS NULL "
                "OR TRIM(workspace_id) = ''"
            )
        ),
        {
            "workspace_id":
                DEFAULT_WORKSPACE_ID,
        },
    )


def apply_workspace_foundation(
    connection: Connection,
) -> None:
    _create_foundation_tables(
        connection
    )

    for table_name in REQUIRED_SCOPED_TABLES:
        _add_workspace_column(
            connection,
            table_name,
            default_to_workspace=True,
        )

        _create_workspace_index(
            connection,
            table_name,
        )

    for table_name in OPTIONAL_SCOPED_TABLES:
        _add_workspace_column(
            connection,
            table_name,
            default_to_workspace=False,
        )

        _create_workspace_index(
            connection,
            table_name,
        )

    _seed_default_workspace(
        connection
    )

    _seed_default_memberships(
        connection
    )

    for table_name in REQUIRED_SCOPED_TABLES:
        _backfill_required_table(
            connection,
            table_name,
        )


def validate_workspace_foundation(
    connection: Connection,
) -> None:
    tables = _table_names(
        connection
    )

    required_foundation = {
        "workspace",
        "workspace_membership",
        "user",
    }

    missing_foundation = (
        required_foundation
        - tables
    )

    if missing_foundation:
        raise WorkspaceFoundationMigrationError(
            "Workspace foundation tables are missing: "
            + ", ".join(
                sorted(
                    missing_foundation
                )
            )
        )

    workspace_table = Workspace.__table__
    membership_table = (
        WorkspaceMembership.__table__
    )
    user_table = User.__table__

    default_workspace = connection.execute(
        select(
            workspace_table.c.status
        ).where(
            workspace_table.c.id
            == DEFAULT_WORKSPACE_ID
        )
    ).scalar_one_or_none()

    if default_workspace != "active":
        raise WorkspaceFoundationMigrationError(
            "The default workspace is missing or inactive."
        )

    user_ids = connection.execute(
        select(
            user_table.c.id
        )
    ).scalars().all()

    for user_id in user_ids:
        membership = connection.execute(
            select(
                membership_table.c.id
            ).where(
                membership_table.c.workspace_id
                == DEFAULT_WORKSPACE_ID,
                membership_table.c.user_id
                == user_id,
                membership_table.c.status
                == "active",
                membership_table.c.is_default
                .is_(True),
            )
        ).first()

        if membership is None:
            raise WorkspaceFoundationMigrationError(
                "A user does not have an active "
                "default workspace membership."
            )

    duplicate_memberships = connection.execute(
        text(
            """
            SELECT
                workspace_id,
                user_id,
                COUNT(*) AS membership_count
            FROM workspace_membership
            GROUP BY workspace_id, user_id
            HAVING COUNT(*) > 1
            """
        )
    ).first()

    if duplicate_memberships is not None:
        raise WorkspaceFoundationMigrationError(
            "Duplicate workspace membership exists."
        )

    for table_name in REQUIRED_SCOPED_TABLES:
        if table_name not in tables:
            continue

        if "workspace_id" not in _column_names(
            connection,
            table_name,
        ):
            raise WorkspaceFoundationMigrationError(
                "Required workspace column is missing "
                f"from {table_name}."
            )

        quoted_table = _quote_identifier(
            connection,
            table_name,
        )

        unscoped_count = connection.execute(
            text(
                (
                    f"SELECT COUNT(*) "
                    f"FROM {quoted_table} "
                    "WHERE workspace_id IS NULL "
                    "OR TRIM(workspace_id) = ''"
                )
            )
        ).scalar_one()

        if int(unscoped_count) != 0:
            raise WorkspaceFoundationMigrationError(
                "Unscoped records remain in "
                f"{table_name}."
            )

    for table_name in OPTIONAL_SCOPED_TABLES:
        if table_name not in tables:
            continue

        if "workspace_id" not in _column_names(
            connection,
            table_name,
        ):
            raise WorkspaceFoundationMigrationError(
                "Optional workspace-context column "
                f"is missing from {table_name}."
            )


PWI_001_WORKSPACE_FOUNDATION = DatabaseMigration(
    migration_id=MIGRATION_ID,
    checksum=MIGRATION_CHECKSUM,
    apply=apply_workspace_foundation,
    validate=validate_workspace_foundation,
)
