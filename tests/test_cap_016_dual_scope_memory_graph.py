from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy.dialects import sqlite

# Bootstrap the existing Memory model before importing either service.
# memory.py owns late imports of both graph and consolidation services.
import app.db.models.memory  # noqa: F401
import app.services.memory.memory_graph as memory_graph_module
from app.services.memory.consolidation_engine import (
    consolidate_memory,
)
from app.services.memory.memory_graph import (
    link_memories,
)


class ResultRows:
    def first(self):
        return None

    def all(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.statements = []
        self.added = []
        self.commits = 0

    def exec(self, statement):
        self.statements.append(
            statement
        )
        return ResultRows()

    def add(self, record) -> None:
        self.added.append(
            record
        )

    def commit(self) -> None:
        self.commits += 1


def _compiled_sql(
    statement,
) -> str:
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


def _where_clause(
    statement,
) -> str:
    sql = _compiled_sql(
        statement
    )

    return sql.split(
        " where ",
        1,
    )[1]


def test_account_consolidation_is_account_scoped() -> None:
    session = RecordingSession()

    memory = SimpleNamespace(
        id=7,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
        summary="Account task",
        cluster_count=1,
    )

    result = consolidate_memory(
        session,
        memory,
    )

    assert result is memory
    assert len(session.statements) == 1

    where_clause = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-a'"
        in where_clause
    )

    assert (
        "memory.account_user_id = 42"
        in where_clause
    )

    assert (
        "memory.chat_id = 42"
        not in where_clause
    )


def test_legacy_consolidation_retains_chat_scope() -> None:
    session = RecordingSession()

    memory = SimpleNamespace(
        id=8,
        workspace_id="workspace-b",
        chat_id=-100123,
        account_user_id=None,
        summary="Legacy task",
        cluster_count=1,
    )

    result = consolidate_memory(
        session,
        memory,
    )

    assert result is memory
    assert len(session.statements) == 1

    where_clause = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-b'"
        in where_clause
    )

    assert (
        "memory.chat_id = -100123"
        in where_clause
    )

    assert (
        "memory.account_user_id ="
        not in where_clause
    )


def test_account_memory_graph_recent_query_is_account_scoped() -> None:
    session = RecordingSession()

    memory = SimpleNamespace(
        id=9,
        workspace_id="workspace-c",
        chat_id=None,
        account_user_id=51,
        memory_type="task",
        embedding=None,
    )

    link_memories(
        session,
        memory,
    )

    assert len(session.statements) == 1

    where_clause = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-c'"
        in where_clause
    )

    assert (
        "memory.account_user_id = 51"
        in where_clause
    )

    assert (
        "memory.chat_id = 51"
        not in where_clause
    )


def test_legacy_memory_graph_recent_query_retains_chat_scope() -> None:
    session = RecordingSession()

    memory = SimpleNamespace(
        id=10,
        workspace_id="workspace-d",
        chat_id=-100777,
        account_user_id=None,
        memory_type="event",
        embedding=None,
    )

    link_memories(
        session,
        memory,
    )

    assert len(session.statements) == 1

    where_clause = _where_clause(
        session.statements[0]
    )

    assert (
        "memory.workspace_id = "
        "'workspace-d'"
        in where_clause
    )

    assert (
        "memory.chat_id = -100777"
        in where_clause
    )

    assert (
        "memory.account_user_id ="
        not in where_clause
    )


def test_graph_vector_search_receives_same_account_scope(
    monkeypatch,
) -> None:
    session = RecordingSession()
    observed = []

    def fake_vector_search_for_scope(
        *,
        session,
        embedding,
        scope,
        limit,
    ):
        observed.append(
            (
                session,
                embedding,
                scope,
                limit,
            )
        )
        return []

    monkeypatch.setattr(
        memory_graph_module,
        "vector_search_for_scope",
        fake_vector_search_for_scope,
    )

    memory = SimpleNamespace(
        id=11,
        workspace_id="workspace-e",
        chat_id=None,
        account_user_id=61,
        memory_type="decision",
        embedding=[0.1, 0.2],
    )

    link_memories(
        session,
        memory,
    )

    assert len(observed) == 1

    (
        observed_session,
        embedding,
        scope,
        limit,
    ) = observed[0]

    assert observed_session is session
    assert embedding == [0.1, 0.2]
    assert scope.workspace_id == (
        "workspace-e"
    )
    assert scope.account_user_id == 61
    assert scope.chat_id is None
    assert limit == 5


def test_graph_vector_search_preserves_legacy_chat_scope(
    monkeypatch,
) -> None:
    session = RecordingSession()
    observed = []

    def fake_vector_search_for_scope(
        *,
        session,
        embedding,
        scope,
        limit,
    ):
        observed.append(
            (
                session,
                embedding,
                scope,
                limit,
            )
        )
        return []

    monkeypatch.setattr(
        memory_graph_module,
        "vector_search_for_scope",
        fake_vector_search_for_scope,
    )

    memory = SimpleNamespace(
        id=12,
        workspace_id="workspace-f",
        chat_id=-100888,
        account_user_id=None,
        memory_type="task",
        embedding=[0.3, 0.4],
    )

    link_memories(
        session,
        memory,
    )

    assert len(observed) == 1

    scope = observed[0][2]

    assert scope.workspace_id == (
        "workspace-f"
    )
    assert scope.chat_id == -100888
    assert scope.account_user_id is None
