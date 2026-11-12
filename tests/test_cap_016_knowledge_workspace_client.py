from __future__ import annotations

import asyncio
import inspect
import json
import re
from pathlib import Path
from types import SimpleNamespace

from starlette.requests import Request

from app.dashboard.routes import (
    memory_panels,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

DASHBOARD_TEMPLATE = (
    "app/dashboard/templates/dashboard.html"
)


def _source(relative: str) -> str:
    return (
        REPO_ROOT
        / relative
    ).read_text(
        encoding="utf-8",
        errors="strict",
    )


def _javascript_function(
    source: str,
    function_name: str,
) -> str:
    marker = re.search(
        rf"(?:async\s+)?function\s+"
        rf"{re.escape(function_name)}\s*\(",
        source,
    )

    if marker is None:
        raise AssertionError(
            "JavaScript function not found: "
            f"{function_name}"
        )

    brace_start = source.find(
        "{",
        marker.end(),
    )

    if brace_start < 0:
        raise AssertionError(
            "JavaScript function body not found: "
            f"{function_name}"
        )

    depth = 0

    for index in range(
        brace_start,
        len(source),
    ):
        character = source[index]

        if character == "{":
            depth += 1

        elif character == "}":
            depth -= 1

            if depth == 0:
                return source[
                    marker.start():
                    index + 1
                ]

    raise AssertionError(
        "Unterminated JavaScript function: "
        f"{function_name}"
    )


def _principal(
    user_id: str = "42",
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        workspace_id="workspace-a",
        user_id=user_id,
        role="operator",
        permissions=frozenset(
            {
                "manage_memory",
                "view_dashboard",
            }
        ),
        token_id="r14-b-test-token",
    )


class RecordingSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.closed = 0
        self._next_id = 1000

    def add(
        self,
        value: object,
    ) -> None:
        self.added.append(
            value
        )

    def flush(self) -> None:
        if not self.added:
            return

        value = self.added[-1]

        if getattr(
            value,
            "id",
            None,
        ) is None:
            setattr(
                value,
                "id",
                self._next_id,
            )

            self._next_id += 1

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed += 1


def _json_request(
    payload: object,
) -> Request:
    body = json.dumps(
        payload
    ).encode("utf-8")

    delivered = False

    async def receive():
        nonlocal delivered

        if delivered:
            return {
                "type":
                    "http.request",
                "body":
                    b"",
                "more_body":
                    False,
            }

        delivered = True

        return {
            "type":
                "http.request",
            "body":
                body,
            "more_body":
                False,
        }

    return Request(
        {
            "type":
                "http",
            "asgi": {
                "version":
                    "3.0",
            },
            "http_version":
                "1.1",
            "method":
                "POST",
            "scheme":
                "https",
            "path":
                "/dashboard/tasks/breakdown",
            "raw_path":
                b"/dashboard/tasks/breakdown",
            "query_string":
                b"",
            "headers": [
                (
                    b"content-type",
                    b"application/json",
                ),
            ],
            "client":
                ("testclient", 50000),
            "server":
                ("testserver", 443),
        },
        receive,
    )


def test_dashboard_removes_hard_coded_account_identity(
) -> None:
    source = _source(
        DASHBOARD_TEMPLATE
    )

    assert "const userId" not in source
    assert "${userId}" not in source

    assert re.search(
        r"\buserId\b",
        source,
    ) is None


def test_dashboard_uses_account_bound_knowledge_workspace_routes(
) -> None:
    source = _source(
        DASHBOARD_TEMPLATE
    )

    load_memory = _javascript_function(
        source,
        "loadMemory",
    )

    search = _javascript_function(
        source,
        "search",
    )

    deduplicate = _javascript_function(
        source,
        "deduplicate",
    )

    load_insights = _javascript_function(
        source,
        "loadInsights",
    )

    load_next_action = (
        _javascript_function(
            source,
            "loadNextAction",
        )
    )

    load_priorities = (
        _javascript_function(
            source,
            "loadPriorities",
        )
    )

    load_goals = _javascript_function(
        source,
        "loadGoals",
    )

    assert "`/dashboard/tasks`" in (
        load_memory
    )

    assert (
        "`/dashboard/search?"
        "q=${encodeURIComponent(q)}`"
        in search
    )

    assert (
        "`/dashboard/memory/deduplicate`"
        in deduplicate
    )

    assert (
        "`/dashboard/insights`"
        in load_insights
    )

    assert (
        "`/dashboard/product-insights`"
        in load_next_action
    )

    assert (
        "`/dashboard/priorities`"
        in load_priorities
    )

    assert (
        "`/dashboard/goals`"
        in load_goals
    )

    assert (
        "`/dashboard/tasks/create`"
        in source
    )

    prohibited = (
        "/dashboard/tasks/${userId}",
        "/dashboard/search/${userId}",
        (
            "/dashboard/memory/"
            "deduplicate/${userId}"
        ),
        "/dashboard/insights/${userId}",
        "/insights/${userId}",
        "/dashboard/priorities/${userId}",
        "/dashboard/goals/${userId}",
    )

    for marker in prohibited:
        assert marker not in source


def test_next_action_keeps_predictive_insight_contract(
) -> None:
    source = _source(
        DASHBOARD_TEMPLATE
    )

    function = _javascript_function(
        source,
        "loadNextAction",
    )

    assert (
        "/dashboard/product-insights"
        in function
    )

    assert (
        "/dashboard/next-action"
        not in function
    )


def test_client_mutations_preserve_authenticated_csrf_helper(
) -> None:
    source = _source(
        DASHBOARD_TEMPLATE
    )

    assert (
        "cgmsAuthenticatedFetch"
        in source
    )

    for function_name in (
        "complete",
        "removeMemory",
        "reopen",
        "restore",
        "deduplicate",
        "markDone",
        "breakTask",
    ):
        function = _javascript_function(
            source,
            function_name,
        )

        assert (
            "cgmsAuthenticatedFetch"
            in function
        )

    assert (
        "/dashboard/tasks/create"
        in source
    )


def test_reachable_lifecycle_handlers_use_account_guard(
) -> None:
    for function_name in (
        "restore_memory",
        "reopen_memory",
        "complete_memory",
        "delete_memory",
        "breakdown_task",
    ):
        function = getattr(
            memory_panels,
            function_name,
        )

        parameters = set(
            inspect.signature(
                function
            ).parameters
        )

        assert {
            "workspace_id",
            "principal",
        } <= parameters

        source = inspect.getsource(
            function
        )

        assert (
            "_load_mutable_memory_for_principal"
            in source
        )

        assert "workspace_id" in source

    complete_source = inspect.getsource(
        memory_panels.complete_memory
    )

    assert (
        "identity_scope_from_record"
        in complete_source
    )

    assert (
        "_identity_scoped_memories"
        in complete_source
    )

    assert (
        "_load_identity_scoped_memory"
        in complete_source
    )


def test_cross_account_record_mutation_is_denied(
    monkeypatch,
) -> None:
    session = RecordingSession()

    record = SimpleNamespace(
        id=7,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=99,
        status="active",
    )

    monkeypatch.setattr(
        memory_panels,
        "SessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        memory_panels,
        "load_scoped_record",
        (
            lambda *_args, **_kwargs:
            record
        ),
    )

    response = (
        memory_panels.delete_memory(
            7,
            "workspace-a",
            _principal("42"),
        )
    )

    assert response == {
        "error":
            "not found"
    }

    assert record.status == "active"
    assert session.commits == 0
    assert session.added == []
    assert session.closed == 1


def test_legacy_chat_record_mutation_remains_compatible(
    monkeypatch,
) -> None:
    session = RecordingSession()

    record = SimpleNamespace(
        id=8,
        workspace_id="workspace-a",
        chat_id=-5057144508,
        account_user_id=None,
        status="active",
    )

    monkeypatch.setattr(
        memory_panels,
        "SessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        memory_panels,
        "load_scoped_record",
        (
            lambda *_args, **_kwargs:
            record
        ),
    )

    response = (
        memory_panels.delete_memory(
            8,
            "workspace-a",
            _principal("42"),
        )
    )

    assert response == {
        "status":
            "deleted"
    }

    assert record.status == "deleted"
    assert session.commits == 1
    assert session.added == [
        record
    ]
    assert session.closed == 1


def test_account_breakdown_children_inherit_account_identity(
    monkeypatch,
) -> None:
    session = RecordingSession()

    parent = SimpleNamespace(
        id=21,
        workspace_id="workspace-a",
        chat_id=None,
        account_user_id=42,
        summary="Prepare executive review",
    )

    monkeypatch.setattr(
        memory_panels,
        "SessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        memory_panels,
        "_load_mutable_memory_for_principal",
        (
            lambda *_args, **_kwargs:
            parent
        ),
    )

    response = asyncio.run(
        memory_panels.breakdown_task(
            _json_request(
                {
                    "id":
                        parent.id,
                }
            ),
            "workspace-a",
            _principal("42"),
        )
    )

    assert response[
        "status"
    ] == "success"

    assert response[
        "parent_task_id"
    ] == parent.id

    assert len(
        session.added
    ) == 3

    for child in session.added:
        assert (
            child.workspace_id
            == "workspace-a"
        )

        assert (
            child.account_user_id
            == 42
        )

        assert child.chat_id is None

        assert child.depends_on == [
            parent.id
        ]

    assert session.commits == 1
    assert session.closed == 1


def test_legacy_breakdown_children_inherit_chat_identity(
    monkeypatch,
) -> None:
    session = RecordingSession()

    parent = SimpleNamespace(
        id=22,
        workspace_id="workspace-a",
        chat_id=-5057144508,
        account_user_id=None,
        summary="Review market performance",
    )

    monkeypatch.setattr(
        memory_panels,
        "SessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        memory_panels,
        "_load_mutable_memory_for_principal",
        (
            lambda *_args, **_kwargs:
            parent
        ),
    )

    response = asyncio.run(
        memory_panels.breakdown_task(
            _json_request(
                {
                    "id":
                        parent.id,
                }
            ),
            "workspace-a",
            _principal("42"),
        )
    )

    assert response[
        "status"
    ] == "success"

    assert len(
        session.added
    ) == 3

    for child in session.added:
        assert (
            child.workspace_id
            == "workspace-a"
        )

        assert (
            child.chat_id
            == -5057144508
        )

        assert (
            child.account_user_id
            is None
        )

        assert child.depends_on == [
            parent.id
        ]

    assert session.commits == 1
    assert session.closed == 1


def test_task_creation_uses_published_account_endpoint(
) -> None:
    source = _source(
        DASHBOARD_TEMPLATE
    )

    assert (
        "/dashboard/tasks/create"
        in source
    )

    assert (
        "body: JSON.stringify({"
        in source
    )

    assert "summary" in source
