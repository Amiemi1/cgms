from __future__ import annotations

# The Memory model is intentionally imported before the route module.
# ruff: noqa: I001

from types import SimpleNamespace

from sqlalchemy.dialects import sqlite

import app.db.models.memory  # noqa: F401
import app.dashboard.routes.knowledge_workspace as knowledge
from app.services.auth.application_authorization import (
    MANAGE_MEMORY,
    required_permission_for_route,
)
from app.services.auth.auth_dependency import AuthenticatedPrincipal
from app.services.memory.scope import account_scope


class ResultRows:
    def __init__(self, rows) -> None:
        self.rows = list(rows)

    def all(self):
        return list(self.rows)


class RecordingSession:
    def __init__(self, result_sets=None) -> None:
        self.result_sets = list(result_sets or [])
        self.statements = []
        self.added = []
        self.deleted = []
        self.commits = 0
        self.refreshes = 0
        self.closed = 0

    def exec(self, statement):
        self.statements.append(statement)

        rows = (
            self.result_sets.pop(0)
            if self.result_sets
            else []
        )

        return ResultRows(rows)

    def add(self, record) -> None:
        self.added.append(record)

    def delete(self, record) -> None:
        self.deleted.append(record)

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, record) -> None:
        self.refreshes += 1

        if getattr(record, "id", None) is None:
            record.id = 501

    def close(self) -> None:
        self.closed += 1


def _where_clause(statement) -> str:
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


def _principal(
    user_id: str = "42",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user_id,
        workspace_id="workspace-a",
        role="knowledge_worker",
        permissions=frozenset(),
    )


def test_account_scope_comes_from_authenticated_principal() -> None:
    scope = knowledge._account_scope_from_principal(
        _principal()
    )

    assert scope.workspace_id == "workspace-a"
    assert scope.account_user_id == 42
    assert scope.chat_id is None


def test_router_exposes_identity_free_account_paths() -> None:
    observed = {
        (
            method,
            route.path,
        ): route
        for route in knowledge.router.routes
        for method in route.methods
    }

    expected = {
        ("GET", "/dashboard/tasks"),
        ("GET", "/dashboard/search"),
        ("GET", "/dashboard/insights"),
        (
            "GET",
            "/dashboard/product-insights",
        ),
        ("GET", "/dashboard/priorities"),
        ("GET", "/dashboard/goals"),
        (
            "GET",
            "/dashboard/next-action",
        ),
        (
            "POST",
            "/dashboard/tasks/create",
        ),
        (
            "DELETE",
            "/dashboard/memory/deduplicate",
        ),
    }

    assert expected <= set(observed)

    for method, path in expected:
        assert "{chat_id}" not in path
        assert "{user_id}" not in path

        route = observed[
            (
                method,
                path,
            )
        ]

        query_names = {
            parameter.name
            for parameter
            in route.dependant.query_params
        }

        assert "chat_id" not in query_names
        assert "user_id" not in query_names


def test_tasks_query_account_scope_only(
    monkeypatch,
) -> None:
    session = RecordingSession(
        [
            [],
        ]
    )

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    result = knowledge.product_tasks(
        account_scope(
            "workspace-a",
            42,
        )
    )

    assert result == []
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

    assert session.closed == 1


def test_goals_query_account_scope_only(
    monkeypatch,
) -> None:
    session = RecordingSession(
        [
            [],
        ]
    )

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    result = knowledge.product_goals(
        account_scope(
            "workspace-a",
            42,
        ),
        limit=20,
    )

    assert result == []
    assert len(session.statements) == 1

    where_clause = _where_clause(
        session.statements[0]
    )

    assert (
        "goal.workspace_id = "
        "'workspace-a'"
        in where_clause
    )

    assert (
        "goal.account_user_id = 42"
        in where_clause
    )

    assert (
        "goal.chat_id = 42"
        not in where_clause
    )

    assert session.closed == 1


def test_search_forwards_account_scope(
    monkeypatch,
) -> None:
    session = RecordingSession()
    observed = {}

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    def fake_embedding(query):
        assert query == "pricing"
        return [
            0.1,
            0.2,
        ]

    monkeypatch.setattr(
        knowledge,
        "generate_embedding",
        fake_embedding,
    )

    def fake_search(
        *,
        session,
        embedding,
        scope,
        limit,
    ):
        observed.update(
            {
                "session": session,
                "embedding": embedding,
                "scope": scope,
                "limit": limit,
            }
        )

        return [
            {
                "id": 1,
            }
        ]

    monkeypatch.setattr(
        knowledge,
        "search_memories_for_scope",
        fake_search,
    )

    result = knowledge.product_search(
        q="pricing",
        scope=account_scope(
            "workspace-a",
            42,
        ),
    )

    assert result == [
        {
            "id": 1,
        }
    ]

    assert observed["session"] is session
    assert observed["embedding"] == [
        0.1,
        0.2,
    ]

    assert (
        observed[
            "scope"
        ].account_user_id
        == 42
    )

    assert (
        observed[
            "scope"
        ].chat_id
        is None
    )

    assert observed["limit"] == 10
    assert session.closed == 1


def test_panel_and_predictive_insights_keep_account_scope(
    monkeypatch,
) -> None:
    session = RecordingSession()
    observed = {}

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    def fake_priorities(
        session,
        scope,
        limit=10,
    ):
        observed["priority_session"] = session
        observed["priority_scope"] = scope
        observed["priority_limit"] = limit

        return [
            {
                "id": 1,
                "summary": "Review",
                "status": "active",
                "reasons": [],
            }
        ]

    monkeypatch.setattr(
        knowledge,
        "get_prioritized_tasks_for_scope",
        fake_priorities,
    )

    monkeypatch.setattr(
        knowledge,
        "generate_panel_insights",
        lambda tasks: [
            {
                "type": "focus",
                "message": tasks[0]["summary"],
            }
        ],
    )

    def fake_product_insights(scope):
        observed["product_scope"] = scope

        return [
            "Predictive insight",
        ]

    monkeypatch.setattr(
        knowledge,
        "generate_product_insights_for_scope",
        fake_product_insights,
    )

    scope = account_scope(
        "workspace-a",
        42,
    )

    panel_result = knowledge.panel_insights(
        scope
    )

    predictive_result = (
        knowledge.predictive_insights(
            scope
        )
    )

    assert panel_result == [
        {
            "type": "focus",
            "message": "Review",
        }
    ]

    assert predictive_result == {
        "insights": [
            "Predictive insight",
        ]
    }

    assert observed["priority_session"] is session
    assert observed["priority_limit"] == 50

    assert (
        observed[
            "priority_scope"
        ].account_user_id
        == 42
    )

    assert (
        observed[
            "priority_scope"
        ].chat_id
        is None
    )

    assert (
        observed[
            "product_scope"
        ].account_user_id
        == 42
    )

    assert (
        observed[
            "product_scope"
        ].chat_id
        is None
    )

    assert session.closed == 1


def test_priorities_and_next_action_forward_account_scope(
    monkeypatch,
) -> None:
    session = RecordingSession()
    observed = []

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    def fake_priorities(
        session,
        scope,
        limit=10,
    ):
        observed.append(
            (
                "priorities",
                session,
                scope,
                limit,
            )
        )

        return []

    def fake_next_action(
        session,
        scope,
    ):
        observed.append(
            (
                "next",
                session,
                scope,
                None,
            )
        )

        return {
            "summary": "Review pricing",
        }

    monkeypatch.setattr(
        knowledge,
        "get_prioritized_tasks_for_scope",
        fake_priorities,
    )

    monkeypatch.setattr(
        knowledge,
        "get_next_action_for_scope",
        fake_next_action,
    )

    scope = account_scope(
        "workspace-a",
        42,
    )

    assert knowledge.product_priorities(
        scope
    ) == []

    assert knowledge.product_next_action(
        scope
    ) == {
        "summary": "Review pricing",
    }

    assert [
        item[2].account_user_id
        for item in observed
    ] == [
        42,
        42,
    ]

    assert all(
        item[2].chat_id is None
        for item in observed
    )

    assert all(
        item[1] is session
        for item in observed
    )

    assert session.closed == 2


def test_create_task_persists_account_identity_not_chat_identity(
    monkeypatch,
) -> None:
    session = RecordingSession()

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    result = knowledge.create_product_task(
        knowledge.TaskCreateRequest(
            summary=" Review pricing ",
        ),
        account_scope(
            "workspace-a",
            42,
        ),
    )

    assert result["id"] == 501
    assert result["summary"] == "Review pricing"

    assert len(session.added) == 1

    task = session.added[0]

    assert task.workspace_id == "workspace-a"
    assert task.account_user_id == 42
    assert task.chat_id is None
    assert task.memory_type == "task"
    assert task.status == "active"

    assert session.commits == 1
    assert session.refreshes == 1
    assert session.closed == 1


def test_deduplicate_is_account_scoped(
    monkeypatch,
) -> None:
    first = SimpleNamespace(
        summary="Pricing",
    )

    duplicate = SimpleNamespace(
        summary=" pricing ",
    )

    session = RecordingSession(
        [
            [
                first,
                duplicate,
            ]
        ]
    )

    monkeypatch.setattr(
        knowledge,
        "SessionLocal",
        lambda: session,
    )

    result = (
        knowledge.deduplicate_product_memories(
            account_scope(
                "workspace-a",
                42,
            )
        )
    )

    assert result == {
        "deleted": 1,
    }

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

    assert session.deleted == [
        duplicate
    ]

    assert session.commits == 1
    assert session.closed == 1


def test_new_mutations_are_governed_by_manage_memory() -> None:
    assert (
        required_permission_for_route(
            "POST",
            "/dashboard/tasks/create",
        )
        == MANAGE_MEMORY
    )

    assert (
        required_permission_for_route(
            "DELETE",
            "/dashboard/memory/deduplicate",
        )
        == MANAGE_MEMORY
    )
