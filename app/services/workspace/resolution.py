from __future__ import annotations

from dataclasses import dataclass

from app.services.workspace.repository import (
    ActiveWorkspaceMembership,
    WorkspaceRepository,
    get_workspace_repository,
)


@dataclass(frozen=True)
class ResolvedWorkspaceContext:
    workspace_id: str
    workspace_name: str
    user_id: int
    membership_id: int


def _resolved_context(
    result: ActiveWorkspaceMembership,
) -> ResolvedWorkspaceContext:
    return ResolvedWorkspaceContext(
        workspace_id=result.workspace.id,
        workspace_name=result.workspace.name,
        user_id=result.membership.user_id,
        membership_id=result.membership.id,
    )


class WorkspaceContextResolver:
    """
    Resolve authoritative workspace context from persistent state.

    No process-global workspace selection is read or mutated here.
    """

    def __init__(
        self,
        repository: WorkspaceRepository,
    ) -> None:
        self._repository = repository

    def resolve_default(
        self,
        user_id: str | int,
    ) -> ResolvedWorkspaceContext:
        return _resolved_context(
            self._repository
            .resolve_default_membership(
                user_id
            )
        )

    def resolve_requested(
        self,
        *,
        user_id: str | int,
        workspace_id: str,
    ) -> ResolvedWorkspaceContext:
        return _resolved_context(
            self._repository
            .require_active_membership(
                user_id=user_id,
                workspace_id=workspace_id,
            )
        )


def get_workspace_context_resolver(
) -> WorkspaceContextResolver:
    return WorkspaceContextResolver(
        get_workspace_repository()
    )
