from __future__ import annotations

from app.services.workspace.tenant_scope import (
    resolve_legacy_workspace_id,
)


class ProcessGlobalWorkspaceContextRetiredError(
    RuntimeError
):
    """The mutable process-global workspace has been retired."""


def _legacy_connector_workspace() -> dict[str, str]:
    """
    Preserve the explicit governed legacy-ingress contract.

    Browser workspace authority is never sourced here. Authenticated
    browser requests resolve their workspace from the token-bound
    persistent session and active membership instead.
    """
    return {
        "id": resolve_legacy_workspace_id(),
    }


# Import compatibility for legacy connector ingress. This is a fixed,
# explicit transitional scope, not mutable browser or process authority.
get_workspace = _legacy_connector_workspace


__all__ = [
    "ProcessGlobalWorkspaceContextRetiredError",
    "get_workspace",
]
