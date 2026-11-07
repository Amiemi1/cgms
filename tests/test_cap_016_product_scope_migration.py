from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.db.migrations.cap_016_product_scope import (
    CAP_016_PRODUCT_SCOPE,
    MIGRATION_CHECKSUM,
    MIGRATION_ID,
    PRODUCT_SCOPE_TABLES,
    ProductScopeMigrationError,
    _identity_predicate,
    _postgres_statements,
    apply_product_scope,
)


def test_cap016_migration_identity_is_checksum_governed() -> None:
    assert MIGRATION_ID == (
        "20260928_005_cap_016_product_scope"
    )

    assert len(MIGRATION_CHECKSUM) == 64

    assert (
        CAP_016_PRODUCT_SCOPE.migration_id
        == MIGRATION_ID
    )

    assert (
        CAP_016_PRODUCT_SCOPE.checksum
        == MIGRATION_CHECKSUM
    )


def test_cap016_migration_targets_governed_identity_tables() -> None:
    assert tuple(
        spec.table_name
        for spec in PRODUCT_SCOPE_TABLES
    ) == (
        "memory",
        "goal",
        "insight",
    )

    assert {
        spec.table_name:
            spec.identity_mode
        for spec in PRODUCT_SCOPE_TABLES
    } == {
        "memory": "exactly_one",
        "goal": "exactly_one",
        "insight": "at_most_one",
    }


def test_cap016_identity_predicate_is_exactly_one_domain() -> None:
    predicate = (
        " ".join(
            _identity_predicate().split()
        )
    )

    assert (
        "chat_id IS NOT NULL "
        "AND account_user_id IS NULL"
        in predicate
    )

    assert (
        "chat_id IS NULL "
        "AND account_user_id IS NOT NULL"
        in predicate
    )



def test_cap016_insight_predicate_is_at_most_one_domain() -> None:
    predicate = (
        " ".join(
            _identity_predicate(
                "at_most_one"
            ).split()
        )
    )

    assert predicate == (
        "NOT ("
        "chat_id IS NOT NULL "
        "AND account_user_id IS NOT NULL"
        ")"
    )



def test_cap016_postgres_wraps_insight_check_expression() -> None:
    insight_spec = next(
        spec
        for spec in PRODUCT_SCOPE_TABLES
        if spec.table_name == "insight"
    )

    statement = _postgres_statements(
        insight_spec
    )["add_identity_check"]

    normalized = " ".join(
        statement.split()
    )

    assert (
        'CHECK (NOT ('
        'chat_id IS NOT NULL '
        'AND account_user_id IS NOT NULL'
        '))'
        in normalized
    )

    assert (
        'CHECK NOT ('
        not in normalized
    )


@pytest.mark.parametrize(
    "table_name",
    [
        "memory",
        "goal",
        "insight",
    ],
)
def test_cap016_postgres_plan_is_additive_and_non_backfilling(
    table_name: str,
) -> None:
    spec = next(
        spec
        for spec in PRODUCT_SCOPE_TABLES
        if spec.table_name == table_name
    )

    statements = _postgres_statements(
        spec
    )

    combined = "\n".join(
        statements.values()
    )

    assert (
        f'ALTER TABLE "{table_name}" '
        'ADD COLUMN "account_user_id" BIGINT NULL'
        in combined
    )

    assert (
        f'ALTER TABLE "{table_name}" '
        'ALTER COLUMN "chat_id" DROP NOT NULL'
        in combined
    )

    assert (
        'FOREIGN KEY ("account_user_id") '
        'REFERENCES "user" ("id")'
        in combined
    )

    assert "CHECK" in combined

    assert (
        '"account_user_id"'
        in statements[
            "create_account_index"
        ]
    )

    upper = combined.upper()

    assert " UPDATE " not in f" {upper} "
    assert " INSERT " not in f" {upper} "
    assert " DELETE " not in f" {upper} "


class _UnsupportedConnection:
    dialect = SimpleNamespace(
        name="sqlite",
    )


def test_cap016_execution_fails_closed_outside_postgresql() -> None:
    with pytest.raises(
        ProductScopeMigrationError,
        match="requires PostgreSQL",
    ):
        apply_product_scope(
            _UnsupportedConnection()
        )


def test_cap016_migration_does_not_reinterpret_account_as_chat() -> None:
    combined = "\n".join(
        statement
        for spec in PRODUCT_SCOPE_TABLES
        for statement in _postgres_statements(
            spec
        ).values()
    ).lower()

    prohibited = {
        "set chat_id = account_user_id",
        "set account_user_id = chat_id",
        "update memory",
        "update goal",
    }

    assert not any(
        marker in combined
        for marker in prohibited
    )
