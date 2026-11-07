from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Literal

from sqlalchemy import inspect
from sqlalchemy.engine import Connection

from app.db.migrations.runner import DatabaseMigration


MIGRATION_ID = (
    "20260928_005_cap_016_product_scope"
)

_MIGRATION_SIGNATURE = """
CAP-016 first-class browser product identity scope v2
memory goal and insight account_user_id nullable BIGINT foreign key to user.id
memory and goal legacy chat_id changed from required to nullable
insight legacy nullable chat identity preserved
memory and goal exactly-one chat or account identity constraint
insight at-most-one chat or account identity constraint
account identity indexes
no account-to-chat reinterpretation
no historical identity backfill
PostgreSQL governed migration
"""

MIGRATION_CHECKSUM = sha256(
    _MIGRATION_SIGNATURE.encode(
        "utf-8"
    )
).hexdigest()


class ProductScopeMigrationError(RuntimeError):
    """Raised when the CAP-016 product-scope schema is invalid."""


IdentityScopeMode = Literal[
    "exactly_one",
    "at_most_one",
]


@dataclass(frozen=True)
class ProductScopeTableSpec:
    table_name: str
    account_index_name: str
    account_fk_name: str
    identity_check_name: str
    identity_mode: IdentityScopeMode


PRODUCT_SCOPE_TABLES: tuple[
    ProductScopeTableSpec,
    ...,
] = (
    ProductScopeTableSpec(
        table_name="memory",
        account_index_name=(
            "ix_memory_account_user_id"
        ),
        account_fk_name=(
            "fk_memory_account_user_id_user"
        ),
        identity_check_name=(
            "ck_memory_identity_scope_exactly_one"
        ),
        identity_mode="exactly_one",
    ),
    ProductScopeTableSpec(
        table_name="goal",
        account_index_name=(
            "ix_goal_account_user_id"
        ),
        account_fk_name=(
            "fk_goal_account_user_id_user"
        ),
        identity_check_name=(
            "ck_goal_identity_scope_exactly_one"
        ),
        identity_mode="exactly_one",
    ),
    ProductScopeTableSpec(
        table_name="insight",
        account_index_name=(
            "ix_insight_account_user_id"
        ),
        account_fk_name=(
            "fk_insight_account_user_id_user"
        ),
        identity_check_name=(
            "ck_insight_identity_scope_at_most_one"
        ),
        identity_mode="at_most_one",
    ),
)


def _table_names(
    connection: Connection,
) -> set[str]:
    return set(
        inspect(connection).get_table_names()
    )


def _columns(
    connection: Connection,
    table_name: str,
) -> dict[str, dict[str, object]]:
    return {
        str(column["name"]): column
        for column in inspect(
            connection
        ).get_columns(
            table_name
        )
    }


def _index_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(index["name"])
        for index in inspect(
            connection
        ).get_indexes(
            table_name
        )
        if index.get("name")
    }


def _foreign_keys(
    connection: Connection,
    table_name: str,
) -> list[dict[str, object]]:
    return list(
        inspect(
            connection
        ).get_foreign_keys(
            table_name
        )
    )


def _check_names(
    connection: Connection,
    table_name: str,
) -> set[str]:
    return {
        str(check["name"])
        for check in inspect(
            connection
        ).get_check_constraints(
            table_name
        )
        if check.get("name")
    }


def _quote(
    connection: Connection,
    identifier: str,
) -> str:
    return (
        connection.dialect
        .identifier_preparer
        .quote(identifier)
    )


def _require_postgresql(
    connection: Connection,
) -> None:
    dialect = connection.dialect.name

    if dialect != "postgresql":
        raise ProductScopeMigrationError(
            "CAP-016 product-scope migration execution "
            "currently requires PostgreSQL; observed "
            f"{dialect}."
        )


def _require_foundation(
    connection: Connection,
) -> None:
    required = {
        "user",
        "memory",
        "goal",
        "insight",
    }

    missing = (
        required
        - _table_names(
            connection
        )
    )

    if missing:
        raise ProductScopeMigrationError(
            "CAP-016 required tables are missing: "
            + ", ".join(
                sorted(missing)
            )
        )

    for spec in PRODUCT_SCOPE_TABLES:
        columns = _columns(
            connection,
            spec.table_name,
        )

        if "chat_id" not in columns:
            raise ProductScopeMigrationError(
                "Legacy chat identity column is missing "
                f"from {spec.table_name}."
            )


def _identity_predicate(
    identity_mode: IdentityScopeMode = "exactly_one",
) -> str:
    if identity_mode == "exactly_one":
        return (
            "(("
            "chat_id IS NOT NULL "
            "AND account_user_id IS NULL"
            ") OR ("
            "chat_id IS NULL "
            "AND account_user_id IS NOT NULL"
            "))"
        )

    if identity_mode == "at_most_one":
        return (
            "NOT ("
            "chat_id IS NOT NULL "
            "AND account_user_id IS NOT NULL"
            ")"
        )

    raise ProductScopeMigrationError(
        "Unsupported CAP-016 identity mode: "
        f"{identity_mode}"
    )


def _postgres_statements(
    spec: ProductScopeTableSpec,
) -> dict[str, str]:
    table_name = spec.table_name

    return {
        "add_account_column": (
            f'ALTER TABLE "{table_name}" '
            'ADD COLUMN "account_user_id" BIGINT NULL'
        ),
        "drop_chat_not_null": (
            f'ALTER TABLE "{table_name}" '
            'ALTER COLUMN "chat_id" DROP NOT NULL'
        ),
        "create_account_index": (
            "CREATE INDEX IF NOT EXISTS "
            f'"{spec.account_index_name}" '
            f'ON "{table_name}" ("account_user_id")'
        ),
        "add_account_fk": (
            f'ALTER TABLE "{table_name}" '
            f'ADD CONSTRAINT "{spec.account_fk_name}" '
            'FOREIGN KEY ("account_user_id") '
            'REFERENCES "user" ("id")'
        ),
        "add_identity_check": (
            f'ALTER TABLE "{table_name}" '
            f'ADD CONSTRAINT "{spec.identity_check_name}" '
            "CHECK ("
            f"{_identity_predicate(spec.identity_mode)}"
            ")"
        ),
    }


def _invalid_identity_count(
    connection: Connection,
    spec: ProductScopeTableSpec,
) -> int:
    quoted_table = _quote(
        connection,
        spec.table_name,
    )

    if spec.identity_mode == "exactly_one":
        invalid_predicate = (
            "("
            "chat_id IS NULL "
            "AND account_user_id IS NULL"
            ") OR ("
            "chat_id IS NOT NULL "
            "AND account_user_id IS NOT NULL"
            ")"
        )

    elif spec.identity_mode == "at_most_one":
        invalid_predicate = (
            "chat_id IS NOT NULL "
            "AND account_user_id IS NOT NULL"
        )

    else:
        raise ProductScopeMigrationError(
            "Unsupported CAP-016 identity mode: "
            f"{spec.identity_mode}"
        )

    return int(
        connection.exec_driver_sql(
            f"""
            SELECT COUNT(*)
            FROM {quoted_table}
            WHERE {invalid_predicate}
            """
        ).scalar_one()
    )


def _orphan_account_count(
    connection: Connection,
    table_name: str,
) -> int:
    quoted_table = _quote(
        connection,
        table_name,
    )

    return int(
        connection.exec_driver_sql(
            f"""
            SELECT COUNT(*)
            FROM {quoted_table}
            AS scoped_record
            LEFT JOIN "user"
            AS account_record
              ON account_record.id
               = scoped_record.account_user_id
            WHERE scoped_record.account_user_id
                  IS NOT NULL
              AND account_record.id IS NULL
            """
        ).scalar_one()
    )


def _account_foreign_key_exists(
    connection: Connection,
    spec: ProductScopeTableSpec,
) -> bool:
    return any(
        list(
            foreign_key.get(
                "constrained_columns",
                [],
            )
        )
        == ["account_user_id"]
        and foreign_key.get(
            "referred_table"
        )
        == "user"
        and list(
            foreign_key.get(
                "referred_columns",
                [],
            )
        )
        == ["id"]
        for foreign_key in _foreign_keys(
            connection,
            spec.table_name,
        )
    )


def _apply_postgresql_table(
    connection: Connection,
    spec: ProductScopeTableSpec,
) -> None:
    statements = _postgres_statements(
        spec
    )

    columns = _columns(
        connection,
        spec.table_name,
    )

    if "account_user_id" not in columns:
        connection.exec_driver_sql(
            statements[
                "add_account_column"
            ]
        )

    columns = _columns(
        connection,
        spec.table_name,
    )

    if bool(
        columns["chat_id"].get(
            "nullable",
            False,
        )
    ) is False:
        connection.exec_driver_sql(
            statements[
                "drop_chat_not_null"
            ]
        )

    if (
        _invalid_identity_count(
            connection,
            spec,
        )
        != 0
    ):
        raise ProductScopeMigrationError(
            "Existing identity records violate the "
            "CAP-016 identity scope contract in "
            f"{spec.table_name}."
        )

    if (
        _orphan_account_count(
            connection,
            spec.table_name,
        )
        != 0
    ):
        raise ProductScopeMigrationError(
            "Existing CAP-016 account identities are "
            f"orphaned in {spec.table_name}."
        )

    if (
        spec.account_index_name
        not in _index_names(
            connection,
            spec.table_name,
        )
    ):
        connection.exec_driver_sql(
            statements[
                "create_account_index"
            ]
        )

    if not _account_foreign_key_exists(
        connection,
        spec,
    ):
        connection.exec_driver_sql(
            statements[
                "add_account_fk"
            ]
        )

    if (
        spec.identity_check_name
        not in _check_names(
            connection,
            spec.table_name,
        )
    ):
        connection.exec_driver_sql(
            statements[
                "add_identity_check"
            ]
        )


def apply_product_scope(
    connection: Connection,
) -> None:
    """
    Add browser/account identity scope without rewriting legacy identity.

    This migration performs schema changes only. Existing records retain
    their legacy chat_id and receive no inferred account_user_id.
    """
    _require_postgresql(
        connection
    )

    _require_foundation(
        connection
    )

    for spec in PRODUCT_SCOPE_TABLES:
        _apply_postgresql_table(
            connection,
            spec,
        )


def validate_product_scope(
    connection: Connection,
) -> None:
    _require_postgresql(
        connection
    )

    _require_foundation(
        connection
    )

    for spec in PRODUCT_SCOPE_TABLES:
        columns = _columns(
            connection,
            spec.table_name,
        )

        if "account_user_id" not in columns:
            raise ProductScopeMigrationError(
                "CAP-016 account identity column is "
                f"missing from {spec.table_name}."
            )

        if not bool(
            columns["chat_id"].get(
                "nullable",
                False,
            )
        ):
            raise ProductScopeMigrationError(
                "Legacy chat identity remains required "
                f"in {spec.table_name}."
            )

        if not bool(
            columns["account_user_id"].get(
                "nullable",
                False,
            )
        ):
            raise ProductScopeMigrationError(
                "CAP-016 account identity must remain "
                f"nullable in {spec.table_name}."
            )

        if (
            spec.account_index_name
            not in _index_names(
                connection,
                spec.table_name,
            )
        ):
            raise ProductScopeMigrationError(
                "CAP-016 account identity index is "
                f"missing from {spec.table_name}."
            )

        if not _account_foreign_key_exists(
            connection,
            spec,
        ):
            raise ProductScopeMigrationError(
                "CAP-016 account identity foreign key "
                f"is missing from {spec.table_name}."
            )

        if (
            spec.identity_check_name
            not in _check_names(
                connection,
                spec.table_name,
            )
        ):
            raise ProductScopeMigrationError(
                "CAP-016 exactly-one identity constraint "
                f"is missing from {spec.table_name}."
            )

        if (
            _invalid_identity_count(
            connection,
            spec,
        )
            != 0
        ):
            raise ProductScopeMigrationError(
                "CAP-016 identity-scope invariant is "
                f"violated in {spec.table_name}."
            )

        if (
            _orphan_account_count(
                connection,
                spec.table_name,
            )
            != 0
        ):
            raise ProductScopeMigrationError(
                "CAP-016 account identity contains "
                f"orphaned users in {spec.table_name}."
            )


CAP_016_PRODUCT_SCOPE = DatabaseMigration(
    migration_id=MIGRATION_ID,
    checksum=MIGRATION_CHECKSUM,
    apply=apply_product_scope,
    validate=validate_product_scope,
)
