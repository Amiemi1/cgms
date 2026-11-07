from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy.dialects import sqlite

import app.services.intelligence.prioritization_service as prioritization
from app.services.intelligence.prioritization_service import (
    get_next_action,
    get_next_action_for_scope,
    get_prioritized_tasks,
    get_prioritized_tasks_for_scope,
    goal_score,
)
from app.services.memory.scope import (
    account_scope,
)


class ResultRows:
    def all(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.statements = []

    def exec(self, statement):
        self.statements.append(
            statement
        )
        return ResultRows()


def _compiled_sql(statement) -> str:
    compiled = statement.compile(
        dialect=sqlite.dialect(),
        compile_kwargs={
            "literal_binds": True,
        },
    )

    return " ".join(
        str(compiled)
        .lower()
        .split()
    )


def test_account_prioritization_uses_account_identity_only() -> None:
    session = RecordingSession()

    result = get_prioritized_tasks_for_scope(
        session,
        account_scope(
            "workspace-a",
            41,
        ),
    )

    assert result == []
    assert len(session.statements) == 1

    sql = _compiled_sql(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-a'"
        in sql
    )

    assert (
        "memory.account_user_id = 41"
        in sql
    )

    assert "memory.chat_id = 41" not in sql


def test_legacy_prioritization_wrapper_retains_chat_identity() -> None:
    session = RecordingSession()

    result = get_prioritized_tasks(
        session,
        chat_id=-100123,
        workspace_id="workspace-b",
    )

    assert result == []
    assert len(session.statements) == 1

    sql = _compiled_sql(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-b'"
        in sql
    )

    where_clause = sql.split(
        " where ",
        1,
    )[1]

    assert (
        "memory.chat_id = -100123"
        in where_clause
    )

    assert (
        "memory.account_user_id ="
        not in where_clause
    )


def test_account_next_action_passes_account_scope_without_reinterpretation(
    monkeypatch,
) -> None:
    observed = []

    def fake_prioritized(
        session,
        scope,
        limit=10,
    ):
        observed.append(
            (
                scope,
                limit,
            )
        )
        return []

    monkeypatch.setattr(
        prioritization,
        "get_prioritized_tasks_for_scope",
        fake_prioritized,
    )

    result = get_next_action_for_scope(
        object(),
        account_scope(
            "workspace-a",
            77,
        ),
    )

    assert result["summary"] == (
        "No tasks found"
    )

    assert len(observed) == 1

    scope, limit = observed[0]

    assert scope.workspace_id == (
        "workspace-a"
    )
    assert scope.account_user_id == 77
    assert scope.chat_id is None
    assert limit == 50


def test_legacy_next_action_wrapper_builds_legacy_chat_scope(
    monkeypatch,
) -> None:
    observed = []

    def fake_next_action(
        session,
        scope,
    ):
        observed.append(scope)
        return {
            "ok": True,
        }

    monkeypatch.setattr(
        prioritization,
        "get_next_action_for_scope",
        fake_next_action,
    )

    result = get_next_action(
        object(),
        chat_id=-100555,
        workspace_id="workspace-c",
    )

    assert result == {
        "ok": True,
    }

    assert len(observed) == 1

    scope = observed[0]

    assert scope.workspace_id == (
        "workspace-c"
    )
    assert scope.chat_id == -100555
    assert scope.account_user_id is None


def test_goal_score_accepts_same_account_identity(
    monkeypatch,
) -> None:
    memory = SimpleNamespace(
        goal_id=9,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
    )

    goal = SimpleNamespace(
        status="active",
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
    )

    monkeypatch.setattr(
        prioritization,
        "load_scoped_record",
        lambda *_args, **_kwargs: goal,
    )

    assert goal_score(
        object(),
        memory,
    ) == 25


def test_goal_score_rejects_cross_account_identity(
    monkeypatch,
) -> None:
    memory = SimpleNamespace(
        goal_id=9,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
    )

    goal = SimpleNamespace(
        status="active",
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=43,
    )

    monkeypatch.setattr(
        prioritization,
        "load_scoped_record",
        lambda *_args, **_kwargs: goal,
    )

    assert goal_score(
        object(),
        memory,
    ) == 0


def test_goal_score_rejects_cross_identity_domain(
    monkeypatch,
) -> None:
    memory = SimpleNamespace(
        goal_id=9,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
    )

    goal = SimpleNamespace(
        status="active",
        workspace_id="workspace-a",
        chat_id=42,
        account_user_id=None,
    )

    monkeypatch.setattr(
        prioritization,
        "load_scoped_record",
        lambda *_args, **_kwargs: goal,
    )

    assert goal_score(
        object(),
        memory,
    ) == 0
