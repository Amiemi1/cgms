from __future__ import annotations

from pathlib import Path

from app.services.retrieval.vector_search import vector_search
from app.services.search.vector_search_service import search_memories


REPO_ROOT = Path(__file__).resolve().parents[1]


class EmptyResult:
    def fetchall(self):
        return []


class RecordingSession:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, statement, params):
        self.calls.append((statement, params))
        return EmptyResult()


def normalized_sql(statement) -> str:
    return " ".join(str(statement).lower().split())


def test_retrieval_vector_search_binds_workspace_predicate() -> None:
    session = RecordingSession()

    assert vector_search(
        session,
        embedding=[0.1, 0.2],
        chat_id=50,
        workspace_id="workspace-a",
        limit=3,
    ) == []

    statement, params = session.calls[0]
    sql = normalized_sql(statement)

    assert "where workspace_id = :workspace_id" in sql
    assert "and chat_id = :chat_id" in sql
    assert params["workspace_id"] == "workspace-a"
    assert params["chat_id"] == 50
    assert params["limit"] == 3


def test_search_service_binds_workspace_predicate() -> None:
    session = RecordingSession()

    assert search_memories(
        session,
        chat_id=60,
        embedding=[0.3, 0.4],
        workspace_id="workspace-b",
        limit=4,
    ) == []

    statement, params = session.calls[0]
    sql = normalized_sql(statement)

    assert "where workspace_id = :workspace_id" in sql
    assert "and chat_id = :chat_id" in sql
    assert params["workspace_id"] == "workspace-b"
    assert params["chat_id"] == 60
    assert params["limit"] == 4


def test_handler_raw_memory_sql_is_workspace_scoped() -> None:
    source = (
        REPO_ROOT / "app/handlers/intelligence_handler.py"
    ).read_text(encoding="utf-8").lower()

    assert "where workspace_id = :workspace_id" in source
    assert '"workspace_id": workspace_id' in source
