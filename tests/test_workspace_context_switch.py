from __future__ import annotations

import ast
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


def _node_source(
    relative: str,
    *,
    function_name: str,
    class_name: str | None = None,
) -> str:
    source = _source(relative)
    tree = ast.parse(
        source,
        filename=relative,
    )

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if node.name != function_name:
            continue

        if class_name is None:
            return (
                ast.get_source_segment(
                    source,
                    node,
                )
                or ""
            )

        for parent in tree.body:
            if not (
                isinstance(parent, ast.ClassDef)
                and parent.name == class_name
            ):
                continue

            if node in parent.body:
                return (
                    ast.get_source_segment(
                        source,
                        node,
                    )
                    or ""
                )

    raise AssertionError(
        f"Function not found: "
        f"{relative}:{class_name or '<module>'}."
        f"{function_name}"
    )


def _class_fields(
    relative: str,
    *,
    class_name: str,
) -> set[str]:
    source = _source(relative)
    tree = ast.parse(
        source,
        filename=relative,
    )

    for node in tree.body:
        if not (
            isinstance(node, ast.ClassDef)
            and node.name == class_name
        ):
            continue

        fields: set[str] = set()

        for child in node.body:
            if (
                isinstance(child, ast.AnnAssign)
                and isinstance(
                    child.target,
                    ast.Name,
                )
            ):
                fields.add(child.target.id)

        return fields

    raise AssertionError(
        f"Class not found: "
        f"{relative}:{class_name}"
    )


def _function_node(
    relative: str,
    *,
    function_name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
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
            return node

    raise AssertionError(
        f"Function not found: "
        f"{relative}:{function_name}"
    )


def test_foundation_browser_session_jwt_remains_workspace_neutral() -> None:
    fields = _class_fields(
        "app/services/auth/browser_session.py",
        class_name="BrowserSessionIdentity",
    )

    assert "workspace_id" not in fields


def test_foundation_persistent_session_update_is_token_bound() -> None:
    source = _node_source(
        "app/services/auth/session_registry.py",
        class_name="BrowserSessionRegistry",
        function_name="set_workspace",
    )

    assert "identity.token_id" in source
    assert "BrowserSessionRecord.token_id" in source
    assert "record.workspace_id" in source
    assert "normalized_workspace_id" in source
    assert "session.commit" in source


def test_foundation_requested_workspace_requires_active_membership() -> None:
    source = _node_source(
        "app/services/workspace/resolution.py",
        class_name="WorkspaceContextResolver",
        function_name="resolve_requested",
    )

    assert "require_active_membership" in source
    assert "user_id=user_id" in source
    assert "workspace_id=workspace_id" in source


def test_foundation_browser_principal_revalidates_persistent_workspace() -> None:
    dependency = _node_source(
        "app/services/auth/browser_session_dependency.py",
        function_name="get_current_browser_principal",
    )
    authorization = _node_source(
        "app/services/auth/browser_authorization.py",
        function_name="revalidate_browser_session",
    )

    assert "session_registry.require_active" in dependency
    assert 'getattr(' in dependency
    assert '"workspace_id"' in dependency
    assert "revalidate_browser_session" in dependency
    assert "workspace_context_resolver" in dependency

    normalized_authorization = "".join(
        authorization.split()
    )

    assert (
        "workspace_context_resolver.resolve_requested"
        in normalized_authorization
    )
    assert "WorkspaceRepositoryError" in authorization


def test_foundation_workspace_switch_is_already_csrf_governed() -> None:
    source = _source(
        "app/services/auth/application_authorization.py"
    )

    assert '"/workspace/context"' in source
    assert "X-CSRF-Token" in source
    assert "validate_browser_csrf_request" in source


def test_foundation_logout_revokes_persistent_browser_session() -> None:
    source = _node_source(
        "app/dashboard/routes/browser_auth.py",
        function_name="browser_logout",
    )

    assert "session_registry.revoke" in source


def test_foundation_switch_route_does_not_reissue_browser_jwt() -> None:
    source = _node_source(
        "app/dashboard/routes/workspace_context.py",
        function_name="switch",
    )

    assert "issue_browser_session_token" not in source
    assert "set_browser_session_cookie" not in source


def test_contract_switch_uses_authenticated_persistent_browser_session() -> None:
    source = _node_source(
        "app/dashboard/routes/workspace_context.py",
        function_name="switch",
    )

    required = {
        "get_current_browser_principal",
        "get_browser_session_registry",
        "get_workspace_context_resolver",
        "workspace_id",
        "principal",
        "identity",
        "set_workspace",
    }

    missing = {
        item
        for item in required
        if item not in source
    }

    assert not missing, (
        "POST /workspace/context must be driven "
        "by the authenticated persistent browser "
        f"session. Missing markers: {sorted(missing)}"
    )


def test_contract_switch_revalidates_before_persisting_selection() -> None:
    source = _node_source(
        "app/dashboard/routes/workspace_context.py",
        function_name="switch",
    )

    resolve_index = source.find(
        "resolve_requested"
    )
    persist_index = source.find(
        "set_workspace"
    )

    assert resolve_index >= 0
    assert persist_index >= 0
    assert resolve_index < persist_index


def test_contract_switch_denial_is_generic_and_non_disclosing() -> None:
    node = _function_node(
        "app/dashboard/routes/workspace_context.py",
        function_name="switch",
    )

    handlers = [
        handler
        for handler in ast.walk(node)
        if isinstance(
            handler,
            ast.ExceptHandler,
        )
    ]

    repository_handlers = []

    for handler in handlers:
        target = handler.type

        if (
            isinstance(target, ast.Name)
            and target.id
            == "WorkspaceRepositoryError"
        ):
            repository_handlers.append(
                handler
            )

        elif isinstance(
            target,
            ast.Tuple,
        ):
            names = {
                element.id
                for element in target.elts
                if isinstance(
                    element,
                    ast.Name,
                )
            }

            if (
                "WorkspaceRepositoryError"
                in names
            ):
                repository_handlers.append(
                    handler
                )

    assert repository_handlers, (
        "Workspace repository failures must be "
        "caught and translated to a generic denial."
    )

    handler = repository_handlers[0]

    assert any(
        isinstance(child, ast.Raise)
        for child in ast.walk(handler)
    )

    # The denial path must not interpolate the requested
    # workspace ID/name/existence into a client-facing message.
    assert not any(
        isinstance(child, ast.JoinedStr)
        for child in ast.walk(handler)
    )


def test_contract_switch_redirect_accepts_local_targets_only() -> None:
    source = _source(
        "app/dashboard/routes/workspace_context.py"
    )

    assert "_safe_redirect_target" in source

    helper = _node_source(
        "app/dashboard/routes/workspace_context.py",
        function_name="_safe_redirect_target",
    )

    assert (
        "urlsplit" in helper
        or "urlparse" in helper
    )
    assert "/dashboard" in helper
    assert (
        "scheme" in helper
        or "netloc" in helper
        or "startswith(\"//\")" in helper
        or "startswith('//')" in helper
    )


def test_contract_process_global_workspace_authority_is_retired() -> None:
    source = _source(
        "app/services/workspace/context.py"
    )

    assert "CURRENT_WORKSPACE" not in source
    assert "def get_workspace" not in source
    assert "def set_workspace" not in source
