from __future__ import annotations

from sqlalchemy import CheckConstraint

from app.db.models.goal import Goal
from app.db.models.memory import Memory


def _check_constraint_names(
    model,
) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if isinstance(
            constraint,
            CheckConstraint,
        )
        and constraint.name is not None
    }


def _foreign_key_targets(
    model,
    column_name: str,
) -> set[str]:
    column = model.__table__.c[column_name]

    return {
        foreign_key.target_fullname
        for foreign_key in column.foreign_keys
    }


def test_memory_supports_legacy_and_account_identity_columns() -> None:
    table = Memory.__table__

    assert table.c.chat_id.nullable is True
    assert table.c.account_user_id.nullable is True

    assert (
        _foreign_key_targets(
            Memory,
            "account_user_id",
        )
        == {"user.id"}
    )

    assert (
        "ck_memory_identity_scope_exactly_one"
        in _check_constraint_names(
            Memory
        )
    )


def test_goal_supports_legacy_and_account_identity_columns() -> None:
    table = Goal.__table__

    assert table.c.chat_id.nullable is True
    assert table.c.account_user_id.nullable is True

    assert (
        _foreign_key_targets(
            Goal,
            "account_user_id",
        )
        == {"user.id"}
    )

    assert (
        "ck_goal_identity_scope_exactly_one"
        in _check_constraint_names(
            Goal
        )
    )


def test_memory_legacy_chat_constructor_remains_available() -> None:
    memory = Memory(
        workspace_id="workspace-a",
        chat_id=-1001234567890,
        summary="Legacy chat memory",
        memory_type="task",
    )

    assert memory.chat_id == -1001234567890
    assert memory.account_user_id is None


def test_memory_account_constructor_is_distinct_from_chat_identity() -> None:
    memory = Memory(
        workspace_id="workspace-a",
        account_user_id=42,
        summary="Browser product memory",
        memory_type="task",
    )

    assert memory.account_user_id == 42
    assert memory.chat_id is None


def test_goal_legacy_chat_constructor_remains_available() -> None:
    goal = Goal(
        workspace_id="workspace-a",
        chat_id=-1001234567890,
        name="Legacy chat goal",
    )

    assert goal.chat_id == -1001234567890
    assert goal.account_user_id is None


def test_goal_account_constructor_is_distinct_from_chat_identity() -> None:
    goal = Goal(
        workspace_id="workspace-a",
        account_user_id=42,
        name="Browser product goal",
    )

    assert goal.account_user_id == 42
    assert goal.chat_id is None


def test_identity_constraints_do_not_reinterpret_account_id_as_chat_id() -> None:
    memory_columns = set(
        Memory.__table__.c.keys()
    )

    goal_columns = set(
        Goal.__table__.c.keys()
    )

    assert {
        "chat_id",
        "account_user_id",
    }.issubset(memory_columns)

    assert {
        "chat_id",
        "account_user_id",
    }.issubset(goal_columns)

    assert (
        Memory.__table__.c.chat_id
        is not Memory.__table__.c.account_user_id
    )

    assert (
        Goal.__table__.c.chat_id
        is not Goal.__table__.c.account_user_id
    )
