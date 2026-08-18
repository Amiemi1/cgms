from __future__ import annotations

from app.services.workspace.repository import (
    WorkspaceRecord,
    WorkspaceRepository,
    get_workspace_repository,
)


def _workspace_payload(
    workspace: WorkspaceRecord,
) -> dict[str, object]:
    return {
        "name": workspace.name,
        "status": workspace.status,
        "createdBy": workspace.created_by_user_id,
        "createdAt": workspace.created_at.isoformat(),
        "updatedAt": workspace.updated_at.isoformat(),
    }


def get_workspaces(
    repository: WorkspaceRepository | None = None,
) -> dict[str, dict[str, object]]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_repository()
    )

    return {
        workspace.id: _workspace_payload(workspace)
        for workspace in resolved_repository.list_workspaces()
    }


def create_workspace(
    workspace_id: str,
    payload: dict[str, object],
    *,
    created_by_user_id: str | int | None = None,
    repository: WorkspaceRepository | None = None,
) -> dict[str, object]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_repository()
    )
    workspace = resolved_repository.create_workspace(
        workspace_id=workspace_id,
        name=str(payload.get("name") or ""),
        created_by_user_id=created_by_user_id,
        owner_user_id=created_by_user_id,
    )

    return _workspace_payload(workspace)
