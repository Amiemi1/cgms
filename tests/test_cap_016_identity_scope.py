from __future__ import annotations

import pytest

from app.services.memory.scope import (
    IdentityScopeError,
    MemoryIdentityScope,
    account_scope,
    legacy_chat_scope,
    resolve_identity_scope,
)
from app.services.workspace.tenant_scope import (
    TenantScopeError,
)


def test_legacy_chat_scope_preserves_negative_telegram_identity() -> None:
    scope = legacy_chat_scope(
        "Workspace-A",
        -1001234567890,
    )

    assert scope == MemoryIdentityScope(
        workspace_id="workspace-a",
        chat_id=-1001234567890,
    )
    assert scope.kind == "legacy_chat"
    assert scope.account_user_id is None


def test_account_scope_uses_distinct_authenticated_account_domain() -> None:
    scope = account_scope(
        "Workspace-A",
        42,
    )

    assert scope == MemoryIdentityScope(
        workspace_id="workspace-a",
        account_user_id=42,
    )
    assert scope.kind == "account"
    assert scope.chat_id is None


def test_identity_scope_rejects_missing_identity() -> None:
    with pytest.raises(
        IdentityScopeError,
        match="Exactly one identity scope",
    ):
        resolve_identity_scope(
            "workspace-a"
        )


def test_identity_scope_rejects_both_identity_domains() -> None:
    with pytest.raises(
        IdentityScopeError,
        match="Exactly one identity scope",
    ):
        resolve_identity_scope(
            "workspace-a",
            chat_id=7,
            account_user_id=7,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        "7",
        7.0,
        True,
        False,
    ],
)
def test_chat_identity_requires_integer_without_boolean_alias(
    invalid: object,
) -> None:
    with pytest.raises(
        IdentityScopeError,
        match="chat_id must be an integer",
    ):
        legacy_chat_scope(
            "workspace-a",
            invalid,
        )


@pytest.mark.parametrize(
    "invalid",
    [
        -1,
        0,
        "7",
        7.0,
        True,
        False,
    ],
)
def test_account_identity_requires_positive_integer(
    invalid: object,
) -> None:
    with pytest.raises(
        IdentityScopeError,
    ):
        account_scope(
            "workspace-a",
            invalid,
        )


def test_account_identity_is_never_reinterpreted_as_chat_identity() -> None:
    scope = resolve_identity_scope(
        "workspace-a",
        account_user_id=91,
    )

    assert scope.account_user_id == 91
    assert scope.chat_id is None
    assert scope.kind == "account"


def test_legacy_chat_identity_is_never_reinterpreted_as_account_identity() -> None:
    scope = resolve_identity_scope(
        "workspace-a",
        chat_id=91,
    )

    assert scope.chat_id == 91
    assert scope.account_user_id is None
    assert scope.kind == "legacy_chat"


def test_workspace_normalization_is_preserved() -> None:
    scope = account_scope(
        "  Workspace-A  ",
        17,
    )

    assert scope.workspace_id == "workspace-a"


def test_invalid_workspace_fails_closed() -> None:
    with pytest.raises(
        TenantScopeError,
    ):
        account_scope(
            "INVALID WORKSPACE !",
            17,
        )
