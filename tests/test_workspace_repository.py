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
from app.services.workspace.repository import (
    InvalidWorkspaceIdentifierError,
    WorkspaceConflictError,
    WorkspaceMembershipConflictError,
    WorkspaceRepository,
    normalize_workspace_identifier,
    normalize_workspace_name,
)


@pytest.fixture()
def repository():
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

    with Session(engine) as session:
        session.add(
            User(
                id=1001,
                email="admin@example.test",
                password_hash="hash",
            )
        )

        session.add(
            User(
                id=1002,
                email="operator@example.test",
                password_hash="hash",
            )
        )

        session.commit()

    def session_factory():
        return Session(
            engine
        )

    result = WorkspaceRepository(
        session_factory
    )

    yield result

    engine.dispose()


def test_normalizes_workspace_identity_and_name(
) -> None:
    assert (
        normalize_workspace_identifier(
            "  Commercial-Intelligence "
        )
        == "commercial-intelligence"
    )

    assert (
        normalize_workspace_name(
            "  Commercial Intelligence  "
        )
        == "Commercial Intelligence"
    )


def test_rejects_invalid_workspace_identifiers(
) -> None:
    invalid_values = (
        "",
        " ",
        "-workspace",
        "workspace-",
        "workspace_name",
        "workspace/name",
        "a" * 65,
    )

    for value in invalid_values:
        with pytest.raises(
            InvalidWorkspaceIdentifierError
        ):
            normalize_workspace_identifier(
                value
            )


def test_creates_and_lists_persistent_workspaces(
    repository: WorkspaceRepository,
) -> None:
    created = repository.create_workspace(
        workspace_id="commercial-intelligence",
        name="Commercial Intelligence",
        created_by_user_id=1001,
    )

    assert (
        created.id
        == "commercial-intelligence"
    )

    assert created.status == "active"
    assert created.created_by_user_id == 1001

    listed = repository.list_workspaces()

    assert [
        workspace.id
        for workspace in listed
    ] == [
        "commercial-intelligence",
    ]


def test_duplicate_workspace_fails_closed(
    repository: WorkspaceRepository,
) -> None:
    repository.create_workspace(
        workspace_id="default",
        name="Default Workspace",
    )

    with pytest.raises(
        WorkspaceConflictError
    ):
        repository.create_workspace(
            workspace_id="default",
            name="Duplicate Default",
        )


def test_adds_membership_and_rejects_duplicate(
    repository: WorkspaceRepository,
) -> None:
    repository.create_workspace(
        workspace_id="default",
        name="Default Workspace",
    )

    membership = repository.add_membership(
        workspace_id="default",
        user_id=1001,
        is_default=True,
    )

    assert membership.workspace_id == "default"
    assert membership.user_id == 1001
    assert membership.status == "active"
    assert membership.is_default is True

    with pytest.raises(
        WorkspaceMembershipConflictError
    ):
        repository.add_membership(
            workspace_id="default",
            user_id=1001,
        )


def test_setting_default_replaces_previous_default(
    repository: WorkspaceRepository,
) -> None:
    repository.create_workspace(
        workspace_id="default",
        name="Default Workspace",
    )

    repository.create_workspace(
        workspace_id="secondary",
        name="Secondary Workspace",
    )

    repository.add_membership(
        workspace_id="default",
        user_id=1001,
        is_default=True,
    )

    repository.add_membership(
        workspace_id="secondary",
        user_id=1001,
    )

    selected = (
        repository.set_default_membership(
            workspace_id="secondary",
            user_id=1001,
        )
    )

    assert selected.workspace_id == "secondary"
    assert selected.is_default is True

    memberships = (
        repository.list_user_memberships(
            1001
        )
    )

    defaults = [
        membership.workspace_id
        for membership in memberships
        if membership.is_default
    ]

    assert defaults == [
        "secondary",
    ]


def test_workspace_and_membership_status_transitions(
    repository: WorkspaceRepository,
) -> None:
    repository.create_workspace(
        workspace_id="default",
        name="Default Workspace",
    )

    repository.add_membership(
        workspace_id="default",
        user_id=1001,
        is_default=True,
    )

    suspended_workspace = (
        repository.set_workspace_status(
            "default",
            "suspended",
        )
    )

    suspended_membership = (
        repository.set_membership_status(
            workspace_id="default",
            user_id=1001,
            status="suspended",
        )
    )

    assert (
        suspended_workspace.status
        == "suspended"
    )

    assert (
        suspended_membership.status
        == "suspended"
    )
