from __future__ import annotations

import ast
from pathlib import Path

from sqlalchemy.dialects import sqlite

from app.services.intelligence.prioritization_service import (
    get_prioritized_tasks,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

DIRECT_QUERY_PATHS = (
    "app/dashboard/main.py",
    "app/dashboard/routes/goal_api.py",
    "app/dashboard/routes/intelligence_api.py",
    "app/dashboard/routes/memory_actions.py",
    "app/dashboard/routes/memory_graph.py",
    "app/dashboard/routes/memory_intelligence.py",
    "app/dashboard/routes/memory_panels.py",
    "app/services/insights/insight_engine.py",
    "app/services/intelligence/prioritization_service.py",
    "app/services/memory/consolidation_engine.py",
    "app/services/memory/memory_graph.py",
    "app/services/memory_intelligence/events.py",
    "app/services/memory_intelligence/score_store.py",
    "app/services/retrieval/vector_search.py",
    "app/services/search/vector_search_service.py",
)

ROUTE_FUNCTIONS = {
    "app/dashboard/main.py": {"mark_task_complete"},
    "app/dashboard/routes/goal_api.py": {"get_goals"},
    "app/dashboard/routes/insights.py": {"get_insights"},
    "app/dashboard/routes/intelligence_api.py": {
        "next_action",
        "get_intelligence_goals",
        "priorities",
    },
    "app/dashboard/routes/memory_actions.py": {"update_priority"},
    "app/dashboard/routes/memory_graph.py": {"get_memory_graph"},
    "app/dashboard/routes/memory_intelligence.py": {
        "get_memory_intelligence",
        "explain_memory",
        "memory_event",
        "score_cache",
        "all_score_cache",
        "memory_dashboard",
        "memory_intelligence_hook",
    },
    "app/dashboard/routes/memory_panels.py": {
        "get_tasks",
        "get_events",
        "get_decisions",
        "get_insights",
        "restore_memory",
        "reopen_memory",
        "get_timeline",
        "complete_memory",
        "delete_memory",
        "delay_memory",
        "deduplicate_memories",
        "semantic_search",
        "memory_graph",
        "complete_task",
        "breakdown_task",
    },
    "app/web/routers/search_api.py": {"search"},
}

PRODUCER_PATHS = (
    "app/handlers/ingestion_handler.py",
    "app/services/agent/action_engine.py",
    "app/services/agent/learning_engine.py",
    "app/services/graph/vector_graph.py",
    "app/services/ingestion/message_ingestor.py",
    "app/services/insights/insight_engine.py",
    "app/services/insights/proactive_engine.py",
    "app/services/learning/learning_engine.py",
    "app/services/memory/memory_graph.py",
    "app/services/memory/memory_pipeline.py",
    "app/services/memory/save_candidate.py",
    "app/services/memory/save_message.py",
    "app/services/memory_intelligence/score_store.py",
    "app/services/reasoning/decision_lineage_service.py",
    "app/services/security/memory_access_control.py",
)

TENANT_CONSTRUCTOR_NAMES = {
    "CandidateMemory",
    "DecisionLineage",
    "Goal",
    "Insight",
    "Learning",
    "LearningLog",
    "Memory",
    "MemoryAccess",
    "MemoryRelationship",
    "MemoryScore",
    "Message",
}


class ResultRows:
    def all(self):
        return []

    def first(self):
        return None


class RecordingSession:
    def __init__(self) -> None:
        self.statements = []

    def exec(self, statement):
        self.statements.append(statement)
        return ResultRows()


def parse(relative: str) -> ast.Module:
    return ast.parse(
        (REPO_ROOT / relative).read_text(encoding="utf-8"),
        filename=relative,
    )


def function_arguments(tree: ast.Module) -> dict[str, list[set[str]]]:
    result: dict[str, list[set[str]]] = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = {
                argument.arg
                for argument in (
                    node.args.posonlyargs
                    + node.args.args
                    + node.args.kwonlyargs
                )
            }
            result.setdefault(node.name, []).append(arguments)

    return result


def test_all_tenant_routes_require_explicit_workspace_context() -> None:
    for relative, function_names in ROUTE_FUNCTIONS.items():
        signatures = function_arguments(parse(relative))

        for function_name in function_names:
            assert function_name in signatures, (
                relative,
                function_name,
            )
            assert all(
                "workspace_id" in arguments
                for arguments in signatures[function_name]
            ), (relative, function_name, signatures[function_name])


def test_direct_query_paths_do_not_use_unscoped_session_get() -> None:
    for relative in DIRECT_QUERY_PATHS:
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "session.get(" not in source, relative
        assert "db.get(" not in source, relative


def test_tenant_constructors_bind_or_inherit_workspace() -> None:
    observed = []

    for relative in PRODUCER_PATHS:
        tree = parse(relative)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            function_name = None
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr

            if function_name not in TENANT_CONSTRUCTOR_NAMES:
                continue

            keyword_names = {keyword.arg for keyword in node.keywords}
            observed.append((relative, function_name, node.lineno))
            assert (
                "workspace_id" in keyword_names
                or None in keyword_names
            ), (relative, function_name, node.lineno)

    assert observed


def test_prioritization_query_contains_workspace_and_chat_predicates() -> None:
    session = RecordingSession()

    result = get_prioritized_tasks(
        session,
        chat_id=123,
        workspace_id="workspace-a",
    )

    assert result == []
    assert len(session.statements) == 1

    compiled = session.statements[0].compile(
        dialect=sqlite.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = " ".join(str(compiled).lower().split())

    assert "memory.workspace_id = 'workspace-a'" in sql
    assert "memory.chat_id = 123" in sql
