from __future__ import annotations

from app.db.models.workspace_control import (
    DEFAULT_MAX_CONNECTORS,
    DEFAULT_MAX_EVENTS,
    DEFAULT_MAX_USERS,
)
from app.services.workspace.control_repository import (
    WorkspaceControlRepository,
    WorkspaceQuotaRecord,
    get_workspace_control_repository,
)


DEFAULT_QUOTAS = {
    "maxEvents": DEFAULT_MAX_EVENTS,
    "maxConnectors": DEFAULT_MAX_CONNECTORS,
    "maxUsers": DEFAULT_MAX_USERS,
}


def _quota_payload(
    record: WorkspaceQuotaRecord,
) -> dict[str, int]:
    return {
        "maxEvents": record.max_events,
        "maxConnectors": record.max_connectors,
        "maxUsers": record.max_users,
    }


def get_workspace_quotas(
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, dict[str, int]]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )
    return {
        record.workspace_id: _quota_payload(record)
        for record in resolved_repository.list_quotas()
    }


def get_workspace_quota(
    workspace_id: str,
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, int]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )
    return _quota_payload(
        resolved_repository.get_quota(
            workspace_id
        )
    )


def set_workspace_quota(
    workspace_id: str,
    quota: dict[str, object],
    *,
    updated_by_user_id: str | int | None = None,
    repository: WorkspaceControlRepository | None = None,
) -> dict[str, int]:
    resolved_repository = (
        repository
        if repository is not None
        else get_workspace_control_repository()
    )
    return _quota_payload(
        resolved_repository.set_quota(
            workspace_id,
            quota,
            updated_by_user_id=(
                updated_by_user_id
            ),
        )
    )
