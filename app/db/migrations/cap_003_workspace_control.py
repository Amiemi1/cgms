from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import inspect, insert, select
from sqlalchemy.engine import Connection

from app.db.migrations.runner import DatabaseMigration
from app.db.models.workspace import Workspace
from app.db.models.workspace_control import (
    DEFAULT_MAX_CONNECTORS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_MAX_USERS,
    WorkspaceControl,
)


MIGRATION_ID = (
    "20260818_003_cap_003_workspace_control"
)

_MIGRATION_SIGNATURE = """
CAP-003 workspace control-plane convergence v1
workspace_control table
workspace foreign-key authority
persistent lifecycle metadata and quota limits
one control record per persistent workspace
non-negative quota constraints
"""

MIGRATION_CHECKSUM = sha256(
    _MIGRATION_SIGNATURE.encode(
        "utf-8"
    )
).hexdigest()


class WorkspaceControlMigrationError(RuntimeError):
    """Raised when the workspace-control schema is invalid."""


def _table_names(
    connection: Connection,
) -> set[str]:
    return set(
        inspect(connection).get_table_names()
    )


def apply_workspace_control(
    connection: Connection,
) -> None:
    tables = _table_names(connection)

    if "workspace" not in tables:
        raise WorkspaceControlMigrationError(
            "The persistent workspace table must exist before "
            "workspace controls are created."
        )

    WorkspaceControl.__table__.create(
        bind=connection,
        checkfirst=True,
    )

    workspace_table = Workspace.__table__
    control_table = WorkspaceControl.__table__
    workspace_ids = connection.execute(
        select(workspace_table.c.id).order_by(
            workspace_table.c.id
        )
    ).scalars().all()
    now = datetime.now(timezone.utc)

    for workspace_id in workspace_ids:
        existing = connection.execute(
            select(control_table.c.workspace_id).where(
                control_table.c.workspace_id
                == workspace_id
            )
        ).first()

        if existing is not None:
            continue

        connection.execute(
            insert(control_table).values(
                workspace_id=workspace_id,
                suspension_reason=None,
                max_events=DEFAULT_MAX_EVENTS,
                max_connectors=(
                    DEFAULT_MAX_CONNECTORS
                ),
                max_users=DEFAULT_MAX_USERS,
                updated_by_user_id=None,
                created_at=now,
                updated_at=now,
            )
        )


def validate_workspace_control(
    connection: Connection,
) -> None:
    tables = _table_names(connection)

    if "workspace_control" not in tables:
        raise WorkspaceControlMigrationError(
            "The workspace-control table is missing."
        )

    inspector = inspect(connection)
    columns = {
        str(column["name"]): column
        for column in inspector.get_columns(
            "workspace_control"
        )
    }
    required_columns = {
        "workspace_id",
        "suspension_reason",
        "max_events",
        "max_connectors",
        "max_users",
        "updated_by_user_id",
        "created_at",
        "updated_at",
    }
    missing_columns = required_columns - set(columns)

    if missing_columns:
        raise WorkspaceControlMigrationError(
            "Workspace-control columns are missing: "
            + ", ".join(sorted(missing_columns))
        )

    for column_name in (
        "workspace_id",
        "max_events",
        "max_connectors",
        "max_users",
        "created_at",
        "updated_at",
    ):
        if columns[column_name]["nullable"]:
            raise WorkspaceControlMigrationError(
                "Required workspace-control column is nullable: "
                f"{column_name}"
            )

    foreign_keys = inspector.get_foreign_keys(
        "workspace_control"
    )
    workspace_foreign_key = any(
        foreign_key.get("referred_table")
        == "workspace"
        and foreign_key.get("constrained_columns")
        == ["workspace_id"]
        for foreign_key in foreign_keys
    )

    if not workspace_foreign_key:
        raise WorkspaceControlMigrationError(
            "Workspace-control ownership foreign key is missing."
        )

    workspace_table = Workspace.__table__
    control_table = WorkspaceControl.__table__
    missing_control = connection.execute(
        select(workspace_table.c.id).outerjoin(
            control_table,
            control_table.c.workspace_id
            == workspace_table.c.id,
        ).where(
            control_table.c.workspace_id.is_(None)
        )
    ).first()

    if missing_control is not None:
        raise WorkspaceControlMigrationError(
            "A persistent workspace lacks its control record."
        )

    invalid_quota = connection.execute(
        select(control_table.c.workspace_id).where(
            (control_table.c.max_events < 0)
            | (control_table.c.max_connectors < 0)
            | (control_table.c.max_users < 0)
        )
    ).first()

    if invalid_quota is not None:
        raise WorkspaceControlMigrationError(
            "Workspace-control quota values are invalid."
        )


CAP_003_WORKSPACE_CONTROL = DatabaseMigration(
    migration_id=MIGRATION_ID,
    checksum=MIGRATION_CHECKSUM,
    apply=apply_workspace_control,
    validate=validate_workspace_control,
)
