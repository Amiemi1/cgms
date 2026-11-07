from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.services.workspace.tenant_scope import (
    normalize_workspace_id,
)


IdentityScopeKind = Literal[
    "legacy_chat",
    "account",
]


class IdentityScopeError(ValueError):
    """
    Raised when a memory/product identity scope is invalid.

    Telegram/chat identity and authenticated account identity are
    deliberately separate domains and must never be substituted for
    one another.
    """


def _require_integer(
    value: object,
    *,
    field_name: str,
    allow_negative: bool,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise IdentityScopeError(
            f"{field_name} must be an integer."
        )

    if not allow_negative and value <= 0:
        raise IdentityScopeError(
            f"{field_name} must be greater than zero."
        )

    return value


@dataclass(frozen=True)
class MemoryIdentityScope:
    """
    One explicit identity partition inside one persistent workspace.

    Exactly one identity domain is valid:

    - legacy_chat: workspace_id + chat_id
    - account: workspace_id + account_user_id
    """

    workspace_id: str
    chat_id: int | None = None
    account_user_id: int | None = None

    def __post_init__(self) -> None:
        resolved_workspace_id = normalize_workspace_id(
            self.workspace_id
        )

        object.__setattr__(
            self,
            "workspace_id",
            resolved_workspace_id,
        )

        has_chat = self.chat_id is not None
        has_account = self.account_user_id is not None

        if has_chat == has_account:
            raise IdentityScopeError(
                "Exactly one identity scope must be supplied."
            )

        if has_chat:
            resolved_chat_id = _require_integer(
                self.chat_id,
                field_name="chat_id",
                allow_negative=True,
            )

            object.__setattr__(
                self,
                "chat_id",
                resolved_chat_id,
            )

            return

        resolved_account_user_id = _require_integer(
            self.account_user_id,
            field_name="account_user_id",
            allow_negative=False,
        )

        object.__setattr__(
            self,
            "account_user_id",
            resolved_account_user_id,
        )

    @property
    def kind(self) -> IdentityScopeKind:
        if self.chat_id is not None:
            return "legacy_chat"

        return "account"


def legacy_chat_scope(
    workspace_id: object,
    chat_id: object,
) -> MemoryIdentityScope:
    return MemoryIdentityScope(
        workspace_id=normalize_workspace_id(
            workspace_id
        ),
        chat_id=_require_integer(
            chat_id,
            field_name="chat_id",
            allow_negative=True,
        ),
    )


def account_scope(
    workspace_id: object,
    account_user_id: object,
) -> MemoryIdentityScope:
    return MemoryIdentityScope(
        workspace_id=normalize_workspace_id(
            workspace_id
        ),
        account_user_id=_require_integer(
            account_user_id,
            field_name="account_user_id",
            allow_negative=False,
        ),
    )


def resolve_identity_scope(
    workspace_id: object,
    *,
    chat_id: object | None = None,
    account_user_id: object | None = None,
) -> MemoryIdentityScope:
    """
    Resolve one explicit identity scope without cross-domain fallback.

    In particular, account_user_id is never interpreted as chat_id.
    """
    resolved_workspace_id = normalize_workspace_id(
        workspace_id
    )

    has_chat = chat_id is not None
    has_account = account_user_id is not None

    if has_chat == has_account:
        raise IdentityScopeError(
            "Exactly one identity scope must be supplied."
        )

    if has_chat:
        return legacy_chat_scope(
            resolved_workspace_id,
            chat_id,
        )

    return account_scope(
        resolved_workspace_id,
        account_user_id,
    )

def identity_scope_from_record(
    record: object,
) -> MemoryIdentityScope:
    """
    Resolve the persisted identity domain of one scoped record.

    A record containing neither or both identity domains fails closed.
    """
    return resolve_identity_scope(
        getattr(
            record,
            "workspace_id",
            None,
        ),
        chat_id=getattr(
            record,
            "chat_id",
            None,
        ),
        account_user_id=getattr(
            record,
            "account_user_id",
            None,
        ),
    )


def orm_identity_predicate(
    model: Any,
    scope: MemoryIdentityScope,
):
    """
    Build the identity portion of an ORM tenant query.

    Workspace ownership remains a separate mandatory predicate.
    """
    if scope.chat_id is not None:
        return (
            getattr(
                model,
                "chat_id",
            )
            == scope.chat_id
        )

    if scope.account_user_id is None:
        raise IdentityScopeError(
            "Account identity scope is invalid."
        )

    return (
        getattr(
            model,
            "account_user_id",
        )
        == scope.account_user_id
    )


def raw_identity_predicate(
    scope: MemoryIdentityScope,
) -> tuple[
    str,
    dict[str, int],
]:
    """
    Return one internally controlled raw-SQL identity predicate.

    The returned column expression is selected only from the two
    governed identity domains and never from caller-supplied text.
    """
    if scope.chat_id is not None:
        return (
            "chat_id = :chat_id",
            {
                "chat_id":
                    scope.chat_id,
            },
        )

    if scope.account_user_id is None:
        raise IdentityScopeError(
            "Account identity scope is invalid."
        )

    return (
        "account_user_id = :identity_account_user_id",
        {
            "identity_account_user_id":
                scope.account_user_id,
        },
    )

