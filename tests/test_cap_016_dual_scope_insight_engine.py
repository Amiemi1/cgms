from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy.dialects import sqlite

# Bootstrap the existing Memory model and its late service imports.
import app.db.models.memory  # noqa: F401
import app.services.insights.insight_engine as insight_engine
from app.services.insights.insight_engine import (
    generate_insights,
    generate_insights_for_scope,
)
from app.services.memory.scope import (
    account_scope,
)


class ResultRows:
    def __init__(
        self,
        rows,
    ) -> None:
        self.rows = rows

    def all(self):
        return list(
            self.rows
        )


class RecordingSession:
    def __init__(
        self,
        result_sets,
    ) -> None:
        self.result_sets = list(
            result_sets
        )
        self.statements = []
        self.added = []
        self.commits = 0
        self.closed = 0

    def exec(
        self,
        statement,
    ):
        self.statements.append(
            statement
        )

        if not self.result_sets:
            raise AssertionError(
                "Unexpected session.exec call."
            )

        return ResultRows(
            self.result_sets.pop(0)
        )

    def add(
        self,
        record,
    ) -> None:
        self.added.append(
            record
        )

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed += 1


def _where_clause(
    statement,
) -> str:
    compiled = statement.compile(
        dialect=sqlite.dialect(),
        compile_kwargs={
            "literal_binds": True,
        },
    )

    sql = " ".join(
        str(compiled)
        .lower()
        .split()
    )

    return sql.split(
        " where ",
        1,
    )[1]


def _task_memory():
    return SimpleNamespace(
        id=1,
        summary="Review performance",
        memory_type="task",
        reminder_time=None,
    )


def test_account_insight_generation_queries_account_scope_and_persists_account_identity(
    monkeypatch,
) -> None:
    session = RecordingSession(
        [
            [_task_memory()],
            [],
        ]
    )

    monkeypatch.setattr(
        insight_engine,
        "SessionLocal",
        lambda: session,
    )

    result = generate_insights_for_scope(
        account_scope(
            "workspace-a",
            42,
        )
    )

    assert result
    assert len(session.statements) == 2

    memory_where = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-a'"
        in memory_where
    )

    assert (
        "memory.account_user_id = 42"
        in memory_where
    )

    assert (
        "memory.chat_id = 42"
        not in memory_where
    )

    assert session.added

    for record in session.added:
        assert record.workspace_id == (
            "workspace-a"
        )
        assert record.account_user_id == 42
        assert record.chat_id is None

    assert session.commits == 1
    assert session.closed == 1


def test_legacy_chat_insight_generation_preserves_chat_identity(
    monkeypatch,
) -> None:
    session = RecordingSession(
        [
            [_task_memory()],
            [],
        ]
    )

    monkeypatch.setattr(
        insight_engine,
        "SessionLocal",
        lambda: session,
    )

    result = generate_insights(
        chat_id=-100123,
        workspace_id="workspace-b",
    )

    assert result
    assert len(session.statements) == 2

    memory_where = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-b'"
        in memory_where
    )

    assert (
        "memory.chat_id = -100123"
        in memory_where
    )

    assert (
        "memory.account_user_id ="
        not in memory_where
    )

    assert session.added

    for record in session.added:
        assert record.workspace_id == (
            "workspace-b"
        )
        assert record.chat_id == -100123
        assert record.account_user_id is None

    assert session.commits == 1
    assert session.closed == 1


def test_legacy_wrapper_never_reinterprets_chat_id_as_account_id(
    monkeypatch,
) -> None:
    observed = []

    def fake_generate(
        scope,
    ):
        observed.append(
            scope
        )
        return [
            "legacy",
        ]

    monkeypatch.setattr(
        insight_engine,
        "generate_insights_for_scope",
        fake_generate,
    )

    result = generate_insights(
        chat_id=77,
        workspace_id="workspace-c",
    )

    assert result == [
        "legacy",
    ]

    assert len(observed) == 1

    scope = observed[0]

    assert scope.workspace_id == (
        "workspace-c"
    )
    assert scope.chat_id == 77
    assert scope.account_user_id is None
