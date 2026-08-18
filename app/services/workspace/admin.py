from __future__ import annotations

from app.services.workspace.control_repository import (
    WorkspaceAdminRecord,
    WorkspaceControlRepository,
    get_workspace_control_repository,
)


def _admin_payload(
    record: WorkspaceAdminRecord,
) -> dict[str, object]:
    return {
        "suspended": record.suspended,
        "suspensionReason": record.suspension_reason,
        "updatedAt": record.updated_at.isoformat(),
    }


def get_workspace_admin_state(
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, dict[str, object]]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )

    return {
        record.workspace_id: _admin_payload(record)
        for record in resolved_repository.list_admin_state()
    }


def suspend_workspace(
    workspace_id: str,
    reason: str = "manual_admin_action",
    *,
    updated_by_user_id: str | int | None = None,
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, object]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )
    record = resolved_repository.set_workspace_lifecycle(
        workspace_id,
        "suspended",
        suspension_reason=reason,
        updated_by_user_id=updated_by_user_id,
    )
    return _admin_payload(record)


def activate_workspace(
    workspace_id: str,
    *,
    updated_by_user_id: str | int | None = None,
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, object]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )
    record = resolved_repository.set_workspace_lifecycle(
        workspace_id,
        "active",
        updated_by_user_id=updated_by_user_id,
    )
    return _admin_payload(record)
