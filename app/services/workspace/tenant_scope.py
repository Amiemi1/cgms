from __future__ import annotations

import re
from typing import Any, TypeVar

from sqlmodel import Session, SQLModel, select


TenantModel = TypeVar("TenantModel", bound=SQLModel)

DEFAULT_WORKSPACE_ID = "default"

_WORKSPACE_ID_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
)


class TenantScopeError(ValueError):
    """Raised when tenant workspace context is invalid."""


def normalize_workspace_id(workspace_id: object) -> str:
    """Normalize and validate one explicit workspace identifier."""
    if not isinstance(workspace_id, str):
        raise TenantScopeError("Workspace context is invalid.")

    resolved = workspace_id.strip().lower()

    if (
        not resolved
        or len(resolved) > 64
        or _WORKSPACE_ID_PATTERN.fullmatch(resolved) is None
    ):
        raise TenantScopeError("Workspace context is invalid.")

    return resolved


def resolve_legacy_workspace_id() -> str:
    """
    Resolve the governed transitional workspace for legacy ingress.

    Callers must invoke this explicitly. It is not an ambient fallback.
    """
    return normalize_workspace_id(DEFAULT_WORKSPACE_ID)


def get_current_workspace_id(principal: Any) -> str:
    """Resolve the workspace from an already-authorized principal."""
    if principal is None:
        raise TenantScopeError(
            "Authenticated workspace context is required."
        )

    return normalize_workspace_id(
        getattr(principal, "workspace_id", None)
    )


def require_tenant_model(
    model: type[TenantModel],
) -> type[TenantModel]:
    if not hasattr(model, "workspace_id"):
        raise TenantScopeError(
            "The persistence model is not tenant scoped."
        )

    if not hasattr(model, "id"):
        raise TenantScopeError(
            "The persistence model has no record identifier."
        )

    return model


def scoped_select(
    model: type[TenantModel],
    workspace_id: object,
):
    """Create a select statement constrained to one workspace."""
    resolved_model = require_tenant_model(model)
    resolved_workspace = normalize_workspace_id(workspace_id)

    return select(resolved_model).where(
        resolved_model.workspace_id == resolved_workspace
    )


def load_scoped_record(
    session: Session,
    model: type[TenantModel],
    record_id: object,
    workspace_id: object,
) -> TenantModel | None:
    """
    Load a record without disclosing cross-workspace existence.
    """
    resolved_model = require_tenant_model(model)
    statement = scoped_select(
        resolved_model,
        workspace_id,
    ).where(
        resolved_model.id == record_id
    )
    return session.exec(statement).first()


def bind_workspace(
    record: TenantModel,
    workspace_id: object,
) -> TenantModel:
    """Bind a new record to one explicit workspace."""
    resolved_workspace = normalize_workspace_id(workspace_id)
    current = getattr(record, "workspace_id", None)

    if current not in (None, ""):
        current_workspace = normalize_workspace_id(current)

        if current_workspace != resolved_workspace:
            raise TenantScopeError(
                "Tenant ownership conflicts with "
                "the requested workspace."
            )

    setattr(record, "workspace_id", resolved_workspace)
    return record


def inherit_workspace_id(parent_record: Any) -> str:
    """Resolve ownership from an authoritative parent record."""
    return normalize_workspace_id(
        getattr(parent_record, "workspace_id", None)
    )


def belongs_to_workspace(
    record: Any,
    workspace_id: object,
) -> bool:
    """Return whether a record belongs to the explicit workspace."""
    try:
        return (
            inherit_workspace_id(record)
            == normalize_workspace_id(workspace_id)
        )
    except TenantScopeError:
        return False
