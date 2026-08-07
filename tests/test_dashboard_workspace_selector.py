from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (
        REPO_ROOT
        / relative
    ).read_text(
        encoding="utf-8",
        errors="strict",
    )


def _function_source(
    relative: str,
    function_name: str,
) -> str:
    source = _source(relative)
    tree = ast.parse(
        source,
        filename=relative,
    )

    for node in tree.body:
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == function_name
        ):
            return (
                ast.get_source_segment(
                    source,
                    node,
                )
                or ""
            )

    raise AssertionError(
        f"Function not found: "
        f"{relative}:{function_name}"
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
            f"JavaScript function not found: "
            f"{function_name}"
        )

    brace_start = source.find(
        "{",
        marker.end(),
    )

    if brace_start < 0:
        raise AssertionError(
            f"Function body not found: "
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
        f"Unterminated JavaScript function: "
        f"{function_name}"
    )


def test_foundation_dashboard_preserves_authenticated_csrf_helper() -> None:
    source = _source(
        "app/dashboard/templates/dashboard.html"
    )

    assert '"/auth/csrf"' in source
    assert "X-CSRF-Token" in source
    assert "cgmsObtainCsrfToken" in source
    assert "credentials" in source
    assert "same-origin" in source


def test_foundation_step187e_does_not_add_cross_workspace_comparison() -> None:
    sources = "\n".join(
        _source(path).lower()
        for path in (
            "app/dashboard/main.py",
            "app/dashboard/routes/workspace_context.py",
            "app/dashboard/templates/dashboard.html",
            "app/services/workspace/context.py",
        )
    )

    prohibited_markers = {
        "compare_workspaces",
        "compare-workspaces",
        "aggregate_workspaces",
        "aggregate-workspaces",
        "cross_workspace_comparison",
        "cross-workspace-comparison",
    }

    assert not (
        prohibited_markers
        & {
            marker
            for marker in prohibited_markers
            if marker in sources
        }
    )


def test_contract_dashboard_receives_current_and_authorised_workspace_context() -> None:
    source = _function_source(
        "app/dashboard/main.py",
        "dashboard",
    )

    required = {
        "get_current_browser_principal",
        "get_workspace_repository",
        "list_user_memberships",
        "active_only=True",
        "current_workspace_id",
        "workspace_options",
    }

    missing = {
        marker
        for marker in required
        if marker not in source
    }

    assert not missing, (
        "Authenticated dashboard must receive "
        "server-derived current and authorised "
        f"workspace context. Missing: {sorted(missing)}"
    )


def test_contract_selector_renders_server_authorised_options_and_current_workspace() -> None:
    source = _source(
        "app/dashboard/templates/dashboard.html"
    )

    required = {
        'id="cgms-workspace-selector"',
        'name="workspace_id"',
        "workspace_options",
        "current_workspace_id",
    }

    missing = {
        marker
        for marker in required
        if marker not in source
    }

    assert not missing, (
        "Workspace selector must render only "
        "server-authorised options and expose "
        f"the current workspace. Missing: {sorted(missing)}"
    )


def test_contract_workspace_selector_uses_governed_switch_and_full_navigation() -> None:
    source = _source(
        "app/dashboard/templates/dashboard.html"
    )

    function = _javascript_function(
        source,
        "cgmsSwitchWorkspace",
    )

    assert "/workspace/context" in function
    assert "cgmsAuthenticatedFetch" in function
    assert "fetch(" not in function
    assert (
        "window.location.assign" in function
        or "window.location.reload" in function
    ), (
        "A successful workspace switch must "
        "perform a full navigation so in-memory "
        "workspace-sensitive state cannot leak "
        "across the old and new workspace."
    )


def test_contract_workspace_selection_is_not_stored_in_tab_local_state() -> None:
    source = _source(
        "app/dashboard/templates/dashboard.html"
    )

    # Function creation is owned by the expected-red selector contract.
    # Until it exists, there is no workspace-switch client state to inspect.
    if not re.search(
        r"(?:async\s+)?function\s+cgmsSwitchWorkspace\s*\(",
        source,
    ):
        return

    function = _javascript_function(
        source,
        "cgmsSwitchWorkspace",
    )

    assert "localStorage" not in function
    assert "sessionStorage" not in function
