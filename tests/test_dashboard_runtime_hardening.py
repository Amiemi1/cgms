from __future__ import annotations

import ast
from pathlib import Path

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.dashboard.main import (
    app,
    lifespan,
)


MAIN_PATH = Path(
    "app/dashboard/main.py"
)


def _main_tree() -> ast.Module:
    return ast.parse(
        MAIN_PATH.read_text(
            encoding="utf-8-sig"
        ),
        filename=str(MAIN_PATH),
    )


def test_dashboard_has_one_canonical_lifespan_definition(
) -> None:
    definitions = [
        node
        for node in _main_tree().body
        if (
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            )
            and node.name == "lifespan"
        )
    ]

    assert len(definitions) == 1

    # FastAPI merges the application lifespan with included-router
    # lifespan contexts, so object identity is not a stable contract.
    assert callable(
        app.router.lifespan_context
    )


def test_dashboard_resolves_cors_allowlist_once(
) -> None:
    calls = [
        node
        for node in ast.walk(
            _main_tree()
        )
        if (
            isinstance(node, ast.Call)
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id
            == "get_allowed_cors_origins"
        )
    ]

    assert len(calls) == 1


def test_dashboard_registers_one_cors_middleware(
) -> None:
    cors_entries = [
        middleware
        for middleware in app.user_middleware
        if middleware.cls is CORSMiddleware
    ]

    assert len(cors_entries) == 1


def test_dashboard_exposes_runtime_state_contract(
) -> None:
    source = MAIN_PATH.read_text(
        encoding="utf-8-sig"
    )

    assert (
        "app.state.runtime_environment"
        in source
    )

    assert (
        "app.state.database_schema_ready"
        in source
    )

    assert (
        "initialize_database_schema"
        in source
    )
