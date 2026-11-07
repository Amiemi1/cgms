from __future__ import annotations

from sqlalchemy import CheckConstraint

from app.db.models.insight import Insight


def _check_names() -> set[str]:
    return {
        constraint.name
        for constraint in Insight.__table__.constraints
        if isinstance(
            constraint,
            CheckConstraint,
        )
        and constraint.name is not None
    }


def test_insight_supports_optional_chat_and_account_identity() -> None:
    table = Insight.__table__

    assert table.c.chat_id.nullable is True
    assert table.c.account_user_id.nullable is True

    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key
        in table.c.account_user_id.foreign_keys
    }

    assert foreign_keys == {
        "user.id",
    }

    assert (
        "ck_insight_identity_scope_at_most_one"
        in _check_names()
    )


def test_legacy_chat_insight_constructor_remains_available() -> None:
    insight = Insight(
        workspace_id="workspace-a",
        chat_id=-100123,
        message="Legacy insight",
        insight_type="predictive",
    )

    assert insight.chat_id == -100123
    assert insight.account_user_id is None


def test_account_insight_constructor_is_distinct() -> None:
    insight = Insight(
        workspace_id="workspace-a",
        account_user_id=42,
        message="Account insight",
        insight_type="predictive",
    )

    assert insight.chat_id is None
    assert insight.account_user_id == 42


def test_workspace_level_legacy_insight_remains_representable() -> None:
    insight = Insight(
        workspace_id="workspace-a",
        message="Workspace insight",
        insight_type="predictive",
    )

    assert insight.chat_id is None
    assert insight.account_user_id is None
