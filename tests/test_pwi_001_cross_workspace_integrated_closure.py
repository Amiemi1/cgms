from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


GOVERNED_ROUTE_FUNCTIONS = {
    "app/dashboard/main.py": {
        "mark_task_complete",
    },
    "app/dashboard/routes/goal_api.py": {
        "get_goals",
    },
    "app/dashboard/routes/insights.py": {
        "get_insights",
    },
    "app/dashboard/routes/intelligence_api.py": {
        "next_action",
        "get_intelligence_goals",
        "priorities",
    },
    "app/dashboard/routes/memory_actions.py": {
        "update_priority",
    },
    "app/dashboard/routes/memory_graph.py": {
        "get_memory_graph",
    },
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
    "app/web/routers/search_api.py": {
        "search",
    },
}


def _source(relative: str) -> str:
    return (
        REPO_ROOT
        / relative
    ).read_text(
        encoding="utf-8",
        errors="strict",
    )


def _tree(relative: str) -> ast.Module:
    return ast.parse(
        _source(relative),
        filename=relative,
    )


def _top_level_functions(
    relative: str,
    function_name: str,
) -> list[
    ast.FunctionDef
    | ast.AsyncFunctionDef
]:
    return [
        node
        for node in _tree(relative).body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name == function_name
    ]


def _arguments(
    node: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> set[str]:
    return {
        argument.arg
        for argument in (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
        )
    }


def _workspace_loads(
    node: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[int]:
    return [
        child.lineno
        for child in ast.walk(node)
        if isinstance(child, ast.Name)
        and child.id == "workspace_id"
        and isinstance(child.ctx, ast.Load)
    ]


def _route_identity(
    node: ast.FunctionDef
    | ast.AsyncFunctionDef,
) -> list[tuple[str, str]]:
    identities = []

    for decorator in node.decorator_list:
        if not isinstance(
            decorator,
            ast.Call,
        ):
            continue

        if not isinstance(
            decorator.func,
            ast.Attribute,
        ):
            continue

        method = decorator.func.attr.upper()

        if method not in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }:
            continue

        if not decorator.args:
            continue

        path = decorator.args[0]

        if not (
            isinstance(path, ast.Constant)
            and isinstance(path.value, str)
        ):
            continue

        identities.append(
            (
                method,
                path.value,
            )
        )

    return identities


def _test_names(relative: str) -> set[str]:
    return {
        node.name
        for node in _tree(relative).body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name.startswith("test_")
    }


def test_integrated_next_action_route_is_unique_and_workspace_bound() -> None:
    relative = (
        "app/dashboard/routes/intelligence_api.py"
    )

    matches = _top_level_functions(
        relative,
        "next_action",
    )

    assert len(matches) == 1, (
        "Step 187F requires exactly one "
        "next_action route implementation; "
        f"observed {len(matches)}."
    )

    function = matches[0]

    assert "workspace_id" in _arguments(
        function
    )

    assert _workspace_loads(
        function
    )

    assert (
        "GET",
        "/next-action/{chat_id}",
    ) in _route_identity(
        function
    )

    source = ast.get_source_segment(
        _source(relative),
        function,
    ) or ""

    assert "get_prioritized_tasks" in source
    assert "get_next_action" in source
    assert "workspace_id" in source


def test_integrated_governed_tenant_routes_have_one_workspace_aware_definition() -> None:
    observed = 0

    for (
        relative,
        function_names,
    ) in GOVERNED_ROUTE_FUNCTIONS.items():
        for function_name in function_names:
            matches = _top_level_functions(
                relative,
                function_name,
            )

            assert len(matches) == 1, (
                relative,
                function_name,
                len(matches),
            )

            function = matches[0]

            assert (
                "workspace_id"
                in _arguments(function)
            ), (
                relative,
                function_name,
                "workspace signature missing",
            )

            assert _workspace_loads(
                function
            ), (
                relative,
                function_name,
                "workspace context accepted but unused",
            )

            observed += 1

    assert observed == 31


def test_integrated_browser_and_bearer_workspace_contracts_remain_explicit() -> None:
    required_tests = {
        "tests/test_workspace_bound_authentication.py": {
            "test_bearer_principal_is_workspace_bound",
            "test_bearer_without_workspace_fails_closed",
            "test_bearer_inactive_membership_fails_closed",
            "test_browser_principal_uses_persistent_workspace",
            "test_browser_workspace_denial_is_non_disclosing",
            "test_browser_jwt_remains_workspace_neutral",
        },
        "tests/test_workspace_context_switch.py": {
            "test_foundation_persistent_session_update_is_token_bound",
            "test_foundation_requested_workspace_requires_active_membership",
            "test_foundation_browser_principal_revalidates_persistent_workspace",
            "test_contract_switch_uses_authenticated_persistent_browser_session",
            "test_contract_switch_denial_is_generic_and_non_disclosing",
            "test_contract_process_global_workspace_authority_is_retired",
        },
    }

    for relative, expected in required_tests.items():
        observed = _test_names(
            relative
        )

        assert expected <= observed, (
            relative,
            sorted(
                expected - observed
            ),
        )


def test_integrated_cross_workspace_read_and_raw_sql_denial_contracts_remain_present() -> None:
    required_tests = {
        "tests/test_tenant_record_denial.py": {
            "test_missing_and_cross_workspace_records_share_denial_contract",
        },
        "tests/test_tenant_raw_sql_isolation.py": {
            "test_retrieval_vector_search_binds_workspace_predicate",
            "test_search_service_binds_workspace_predicate",
            "test_handler_raw_memory_sql_is_workspace_scoped",
        },
        "tests/test_tenant_query_isolation.py": {
            "test_all_tenant_routes_require_explicit_workspace_context",
            "test_direct_query_paths_do_not_use_unscoped_session_get",
            "test_tenant_constructors_bind_or_inherit_workspace",
            "test_prioritization_query_contains_workspace_and_chat_predicates",
        },
    }

    for relative, expected in required_tests.items():
        observed = _test_names(
            relative
        )

        assert expected <= observed, (
            relative,
            sorted(
                expected - observed
            ),
        )


def test_integrated_transport_policy_does_not_fallback_from_explicit_bearer_to_browser() -> None:
    source = _source(
        "app/services/auth/application_authorization.py"
    )

    required = {
        'request.headers.get(',
        '"authorization"',
        'transport_policy == "dual"',
        "get_current_principal",
        "get_current_browser_principal",
        "workspace_context_resolver",
        "browser_transport_required",
    }

    missing = {
        marker
        for marker in required
        if marker not in source
    }

    assert not missing, (
        "Application authorization transport "
        f"contract missing markers: {sorted(missing)}"
    )

    bearer_index = source.find(
        "get_current_principal("
    )

    browser_index = source.find(
        "get_current_browser_principal("
    )

    assert bearer_index >= 0
    assert browser_index >= 0
    assert bearer_index != browser_index


def test_integrated_migration_closure_contract_inventory_remains_present() -> None:
    required_tests = {
        "tests/test_workspace_foundation_migration.py": {
            "test_default_migration_inventory_is_ordered",
            "test_foundation_migration_is_idempotent",
            "test_foundation_migration_seeds_and_backfills",
            "test_migration_checksum_mismatch_fails_closed",
            "test_transitional_default_scopes_new_rows",
        },
        "tests/test_pwi_001_tenant_persistence_migration.py": {
            "test_backfills_validates_and_is_idempotent",
            "test_contract_identity_is_checksum_governed",
            "test_enforcement_blocks_invalid_future_ownership",
            "test_missing_required_table_fails_closed",
            "test_orphaned_ownership_fails_validation",
        },
    }

    for relative, expected in required_tests.items():
        observed = _test_names(
            relative
        )

        assert expected <= observed, (
            relative,
            sorted(
                expected - observed
            ),
        )


def test_integrated_process_global_workspace_fallback_remains_retired() -> None:
    context_source = _source(
        "app/services/workspace/context.py"
    )

    tenant_scope_source = _source(
        "app/services/workspace/tenant_scope.py"
    )

    assert "CURRENT_WORKSPACE" not in context_source
    assert "def get_workspace" not in context_source
    assert "def set_workspace" not in context_source

    required = {
        "normalize_workspace_id",
        "get_current_workspace_id",
        "scoped_select",
        "load_scoped_record",
        "bind_workspace",
        "inherit_workspace_id",
        "belongs_to_workspace",
    }

    missing = {
        marker
        for marker in required
        if f"def {marker}" not in tenant_scope_source
    }

    assert not missing, (
        f"Tenant-scope primitives missing: {sorted(missing)}"
    )
