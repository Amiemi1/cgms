from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import (
    Session,
    create_engine,
)

from app.db.models.user import User
from app.db.models.workspace import (
    Workspace,
    WorkspaceMembership,
)
from app.db.models.workspace_control import (
    WorkspaceControl,
)
from app.services.workspace.repository import (
    WorkspaceInactiveError,
    WorkspaceMembershipInactiveError,
    WorkspaceMembershipNotFoundError,
    WorkspaceRepository,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
)


@pytest.fixture()
def resolver():
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    User.__table__.create(
        engine,
        checkfirst=True,
    )

    Workspace.__table__.create(
        engine,
        checkfirst=True,
    )

    WorkspaceMembership.__table__.create(
        engine,
        checkfirst=True,
    )

    WorkspaceControl.__table__.create(
        engine,
        checkfirst=True,
    )

    with Session(engine) as session:
        session.add(
            User(
                id=2001,
                email="viewer@example.test",
                password_hash="hash",
            )
        )

        session.add(
            User(
                id=2002,
                email="outsider@example.test",
                password_hash="hash",
            )
        )

        session.commit()

    def session_factory():
        return Session(
            engine
        )

    repository = WorkspaceRepository(
        session_factory
    )

    repository.create_workspace(
        workspace_id="default",
        name="Default Workspace",
    )

    repository.create_workspace(
        workspace_id="commercial-intelligence",
        name="Commercial Intelligence",
    )

    repository.add_membership(
        workspace_id="default",
        user_id=2001,
        is_default=True,
    )

    repository.add_membership(
        workspace_id="commercial-intelligence",
        user_id=2001,
    )

    result = (
        WorkspaceContextResolver(
            repository
        ),
        repository,
    )

    yield result

    engine.dispose()


def test_resolves_active_default_workspace(
    resolver,
) -> None:
    context_resolver, _ = resolver

    context = (
        context_resolver.resolve_default(
            2001
        )
    )

    assert context.workspace_id == "default"
    assert context.user_id == 2001
    assert context.membership_id > 0


def test_resolves_requested_active_workspace(
    resolver,
) -> None:
    context_resolver, _ = resolver

    context = (
        context_resolver.resolve_requested(
            user_id=2001,
            workspace_id=(
                "commercial-intelligence"
            ),
        )
    )

    assert (
        context.workspace_id
        == "commercial-intelligence"
    )

    assert (
        context.workspace_name
        == "Commercial Intelligence"
    )


def test_missing_membership_fails_closed(
    resolver,
) -> None:
    context_resolver, _ = resolver

    with pytest.raises(
        WorkspaceMembershipNotFoundError
    ):
        context_resolver.resolve_requested(
            user_id=2002,
            workspace_id="default",
        )


def test_suspended_membership_fails_closed(
    resolver,
) -> None:
    context_resolver, repository = resolver

    repository.set_membership_status(
        workspace_id="default",
        user_id=2001,
        status="suspended",
    )

    with pytest.raises(
        WorkspaceMembershipInactiveError
    ):
        context_resolver.resolve_default(
            2001
        )


def test_suspended_workspace_fails_closed(
    resolver,
) -> None:
    context_resolver, repository = resolver

    repository.set_workspace_status(
        "commercial-intelligence",
        "suspended",
    )

    with pytest.raises(
        WorkspaceInactiveError
    ):
        context_resolver.resolve_requested(
            user_id=2001,
            workspace_id=(
                "commercial-intelligence"
            ),
        )
