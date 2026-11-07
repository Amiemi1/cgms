from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy.dialects import sqlite
from sqlmodel import select

from app.db.models.memory import Memory
from app.services.memory.scope import (
    account_scope,
    identity_scope_from_record,
    legacy_chat_scope,
    orm_identity_predicate,
    raw_identity_predicate,
)
from app.services.retrieval.vector_search import (
    vector_search,
    vector_search_for_scope,
)
from app.services.search.vector_search_service import (
    search_memories,
    search_memories_for_scope,
)


class EmptyResult:
    def fetchall(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.calls = []

    def execute(
        self,
        statement,
        params,
    ):
        self.calls.append(
            (
                statement,
                params,
            )
        )
        return EmptyResult()


def _normalized_sql(
    statement,
) -> str:
    return " ".join(
        str(statement)
        .lower()
        .split()
    )


def test_scope_from_record_preserves_legacy_chat_domain() -> None:
    scope = identity_scope_from_record(
        SimpleNamespace(
            workspace_id="Workspace-A",
            chat_id=-100123,
            account_user_id=None,
        )
    )

    assert scope.workspace_id == "workspace-a"
    assert scope.chat_id == -100123
    assert scope.account_user_id is None
    assert scope.kind == "legacy_chat"


def test_scope_from_record_preserves_account_domain() -> None:
    scope = identity_scope_from_record(
        SimpleNamespace(
            workspace_id="Workspace-A",
            chat_id=None,
            account_user_id=42,
        )
    )

    assert scope.workspace_id == "workspace-a"
    assert scope.chat_id is None
    assert scope.account_user_id == 42
    assert scope.kind == "account"


def test_raw_identity_predicate_is_domain_specific() -> None:
    chat_sql, chat_params = (
        raw_identity_predicate(
            legacy_chat_scope(
                "workspace-a",
                -77,
            )
        )
    )

    account_sql, account_params = (
        raw_identity_predicate(
            account_scope(
                "workspace-a",
                77,
            )
        )
    )

    assert chat_sql == (
        "chat_id = :chat_id"
    )
    assert chat_params == {
        "chat_id": -77,
    }

    assert account_sql == (
        "account_user_id = "
        ":identity_account_user_id"
    )
    assert account_params == {
        "identity_account_user_id": 77,
    }


def test_orm_identity_predicate_selects_only_account_domain() -> None:
    scope = account_scope(
        "workspace-a",
        41,
    )

    statement = select(
        Memory
    ).where(
        Memory.workspace_id
        == scope.workspace_id,
        orm_identity_predicate(
            Memory,
            scope,
        ),
    )

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


def test_vector_search_account_scope_binds_account_not_chat() -> None:
    session = RecordingSession()

    result = vector_search_for_scope(
        session=session,
        embedding=[0.1, 0.2],
        scope=account_scope(
            "workspace-a",
            91,
        ),
        limit=3,
    )

    assert result == []
    assert len(session.calls) == 1

    statement, params = session.calls[0]
    sql = _normalized_sql(
        statement
    )

    assert (
        "where workspace_id = "
        ":workspace_id"
        in sql
    )

    assert (
        "and account_user_id = "
        ":identity_account_user_id"
        in sql
    )

    assert "and chat_id =" not in sql

    assert params["workspace_id"] == (
        "workspace-a"
    )
    assert (
        params[
            "identity_account_user_id"
        ]
        == 91
    )
    assert "chat_id" not in params
    assert params["limit"] == 3


def test_semantic_search_account_scope_binds_account_not_chat() -> None:
    session = RecordingSession()

    result = search_memories_for_scope(
        session=session,
        embedding=[0.3, 0.4],
        scope=account_scope(
            "workspace-b",
            92,
        ),
        limit=4,
    )

    assert result == []
    assert len(session.calls) == 1

    statement, params = session.calls[0]
    sql = _normalized_sql(
        statement
    )

    assert (
        "where workspace_id = "
        ":workspace_id"
        in sql
    )

    assert (
        "and account_user_id = "
        ":identity_account_user_id"
        in sql
    )

    assert "and chat_id =" not in sql

    assert params["workspace_id"] == (
        "workspace-b"
    )
    assert (
        params[
            "identity_account_user_id"
        ]
        == 92
    )
    assert "chat_id" not in params
    assert params["limit"] == 4


def test_legacy_vector_search_wrapper_retains_chat_scope() -> None:
    session = RecordingSession()

    assert vector_search(
        session,
        embedding=[0.5, 0.6],
        chat_id=-100500,
        workspace_id="workspace-c",
        limit=2,
    ) == []

    statement, params = session.calls[0]
    sql = _normalized_sql(
        statement
    )

    assert (
        "and chat_id = "
        ":chat_id"
        in sql
    )

    assert "account_user_id =" not in sql
    assert params["chat_id"] == (
        -100500
    )


def test_legacy_semantic_search_wrapper_retains_chat_scope() -> None:
    session = RecordingSession()

    assert search_memories(
        session,
        chat_id=-100600,
        embedding=[0.7, 0.8],
        workspace_id="workspace-d",
        limit=2,
    ) == []

    statement, params = session.calls[0]
    sql = _normalized_sql(
        statement
    )

    assert (
        "and chat_id = "
        ":chat_id"
        in sql
    )

    assert "account_user_id =" not in sql
    assert params["chat_id"] == (
        -100600
    )
