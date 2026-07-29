from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlmodel import Session, select

from app.db.models.user import User
from app.db.models.workspace import (
    Workspace,
    WorkspaceMembership,
    utc_now,
)
from app.db.session import SessionLocal
from app.services.auth.account_authorization import (
    InvalidAccountIdentifierError,
    normalize_account_identifier,
)


WorkspaceStatus = Literal[
    "active",
    "suspended",
]

MembershipStatus = Literal[
    "active",
    "suspended",
]

WORKSPACE_ID_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"
)

VALID_WORKSPACE_STATUSES = frozenset(
    {
        "active",
        "suspended",
    }
)

VALID_MEMBERSHIP_STATUSES = frozenset(
    {
        "active",
        "suspended",
    }
)


class WorkspaceRepositoryError(RuntimeError):
    """Base error for persistent workspace operations."""


class InvalidWorkspaceIdentifierError(
    WorkspaceRepositoryError
):
    """Raised when a workspace identifier is invalid."""


class InvalidWorkspaceNameError(
    WorkspaceRepositoryError
):
    """Raised when a workspace name is invalid."""


class InvalidWorkspaceStatusError(
    WorkspaceRepositoryError
):
    """Raised when a workspace status is invalid."""


class InvalidMembershipStatusError(
    WorkspaceRepositoryError
):
    """Raised when a membership status is invalid."""


class InvalidWorkspaceAccountIdentifierError(
    WorkspaceRepositoryError
):
    """Raised when a workspace account ID is invalid."""


class WorkspaceNotFoundError(
    WorkspaceRepositoryError
):
    """Raised when a workspace does not exist."""


class WorkspaceAccountNotFoundError(
    WorkspaceRepositoryError
):
    """Raised when an account does not exist."""


class WorkspaceConflictError(
    WorkspaceRepositoryError
):
    """Raised when a workspace record already exists."""


class WorkspaceInactiveError(
    WorkspaceRepositoryError
):
    """Raised when a workspace is not active."""


class WorkspaceMembershipNotFoundError(
    WorkspaceRepositoryError
):
    """Raised when an account has no requested membership."""


class WorkspaceMembershipConflictError(
    WorkspaceRepositoryError
):
    """Raised when a membership already exists."""


class WorkspaceMembershipInactiveError(
    WorkspaceRepositoryError
):
    """Raised when a workspace membership is inactive."""


class DefaultWorkspaceResolutionError(
    WorkspaceRepositoryError
):
    """Raised when one active default cannot be resolved."""


class WorkspacePersistenceError(
    WorkspaceRepositoryError
):
    """Raised when workspace persistence fails."""


@dataclass(frozen=True)
class WorkspaceRecord:
    id: str
    name: str
    status: str
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class WorkspaceMembershipRecord:
    id: int
    workspace_id: str
    user_id: int
    status: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ActiveWorkspaceMembership:
    workspace: WorkspaceRecord
    membership: WorkspaceMembershipRecord


def normalize_workspace_identifier(
    value: str,
) -> str:
    if not isinstance(value, str):
        raise InvalidWorkspaceIdentifierError(
            "Workspace identifier must be a string."
        )

    normalized = value.strip().lower()

    if (
        not normalized
        or len(normalized) > 64
        or WORKSPACE_ID_PATTERN.fullmatch(
            normalized
        )
        is None
    ):
        raise InvalidWorkspaceIdentifierError(
            "Workspace identifier must be a lower-case slug "
            "containing only letters, numbers and hyphens."
        )

    return normalized


def normalize_workspace_name(
    value: str,
) -> str:
    if not isinstance(value, str):
        raise InvalidWorkspaceNameError(
            "Workspace name must be a string."
        )

    normalized = value.strip()

    if not normalized or len(normalized) > 160:
        raise InvalidWorkspaceNameError(
            "Workspace name must contain between "
            "1 and 160 characters."
        )

    return normalized


def normalize_workspace_status(
    value: str,
) -> WorkspaceStatus:
    if not isinstance(value, str):
        raise InvalidWorkspaceStatusError(
            "Workspace status must be a string."
        )

    normalized = value.strip().lower()

    if normalized not in VALID_WORKSPACE_STATUSES:
        raise InvalidWorkspaceStatusError(
            "Workspace status must be active or suspended."
        )

    return normalized  # type: ignore[return-value]


def normalize_membership_status(
    value: str,
) -> MembershipStatus:
    if not isinstance(value, str):
        raise InvalidMembershipStatusError(
            "Membership status must be a string."
        )

    normalized = value.strip().lower()

    if normalized not in VALID_MEMBERSHIP_STATUSES:
        raise InvalidMembershipStatusError(
            "Membership status must be active or suspended."
        )

    return normalized  # type: ignore[return-value]


def normalize_workspace_user_id(
    value: str | int,
) -> int:
    try:
        return normalize_account_identifier(
            value
        )

    except InvalidAccountIdentifierError as exc:
        raise InvalidWorkspaceAccountIdentifierError(
            "Workspace account identifier is invalid."
        ) from exc


def _workspace_record(
    model: Workspace,
) -> WorkspaceRecord:
    return WorkspaceRecord(
        id=model.id,
        name=model.name,
        status=model.status,
        created_by_user_id=(
            model.created_by_user_id
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _membership_record(
    model: WorkspaceMembership,
) -> WorkspaceMembershipRecord:
    if model.id is None:
        raise WorkspacePersistenceError(
            "Persisted workspace membership has no ID."
        )

    return WorkspaceMembershipRecord(
        id=model.id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        status=model.status,
        is_default=model.is_default,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class WorkspaceRepository:
    """
    Authoritative persistent workspace and membership repository.

    Application roles remain global. Workspace access is established
    independently through active workspace membership.
    """

    def __init__(
        self,
        session_factory: Callable[
            [],
            Session,
        ] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _load_workspace(
        session: Session,
        workspace_id: str,
    ) -> Workspace:
        workspace = session.exec(
            select(
                Workspace
            ).where(
                Workspace.id
                == workspace_id
            )
        ).first()

        if workspace is None:
            raise WorkspaceNotFoundError(
                "Workspace does not exist."
            )

        return workspace

    @staticmethod
    def _load_account(
        session: Session,
        user_id: int,
    ) -> User:
        account = session.exec(
            select(
                User
            ).where(
                User.id
                == user_id
            )
        ).first()

        if account is None:
            raise WorkspaceAccountNotFoundError(
                "Workspace account does not exist."
            )

        return account

    @staticmethod
    def _load_membership(
        session: Session,
        *,
        workspace_id: str,
        user_id: int,
    ) -> WorkspaceMembership:
        membership = session.exec(
            select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.workspace_id
                == workspace_id,
                WorkspaceMembership.user_id
                == user_id,
            )
        ).first()

        if membership is None:
            raise WorkspaceMembershipNotFoundError(
                "Workspace membership does not exist."
            )

        return membership

    def create_workspace(
        self,
        *,
        workspace_id: str,
        name: str,
        created_by_user_id: (
            str | int | None
        ) = None,
        status: str = "active",
    ) -> WorkspaceRecord:
        normalized_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_name = (
            normalize_workspace_name(
                name
            )
        )

        normalized_status = (
            normalize_workspace_status(
                status
            )
        )

        normalized_creator = (
            normalize_workspace_user_id(
                created_by_user_id
            )
            if created_by_user_id
            is not None
            else None
        )

        session = self._session_factory()

        try:
            existing = session.exec(
                select(
                    Workspace
                ).where(
                    Workspace.id
                    == normalized_id
                )
            ).first()

            if existing is not None:
                raise WorkspaceConflictError(
                    "Workspace already exists."
                )

            if normalized_creator is not None:
                self._load_account(
                    session,
                    normalized_creator,
                )

            now = utc_now()

            workspace = Workspace(
                id=normalized_id,
                name=normalized_name,
                status=normalized_status,
                created_by_user_id=(
                    normalized_creator
                ),
                created_at=now,
                updated_at=now,
            )

            session.add(
                workspace
            )

            try:
                session.commit()
                session.refresh(
                    workspace
                )

            except IntegrityError as exc:
                session.rollback()

                raise WorkspaceConflictError(
                    "Workspace could not be created "
                    "because its identity conflicts."
                ) from exc

            return _workspace_record(
                workspace
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            session.rollback()

            raise WorkspacePersistenceError(
                "Workspace creation failed."
            ) from exc

        finally:
            session.close()

    def list_workspaces(
        self,
        *,
        include_suspended: bool = True,
    ) -> tuple[WorkspaceRecord, ...]:
        session = self._session_factory()

        try:
            statement = select(
                Workspace
            )

            if not include_suspended:
                statement = statement.where(
                    Workspace.status
                    == "active"
                )

            statement = statement.order_by(
                Workspace.id
            )

            workspaces = session.exec(
                statement
            ).all()

            return tuple(
                _workspace_record(
                    workspace
                )
                for workspace in workspaces
            )

        except SQLAlchemyError as exc:
            raise WorkspacePersistenceError(
                "Workspace listing failed."
            ) from exc

        finally:
            session.close()

    def require_workspace(
        self,
        workspace_id: str,
        *,
        require_active: bool = False,
    ) -> WorkspaceRecord:
        normalized_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        session = self._session_factory()

        try:
            workspace = self._load_workspace(
                session,
                normalized_id,
            )

            if (
                require_active
                and workspace.status
                != "active"
            ):
                raise WorkspaceInactiveError(
                    "Workspace is not active."
                )

            return _workspace_record(
                workspace
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            raise WorkspacePersistenceError(
                "Workspace resolution failed."
            ) from exc

        finally:
            session.close()

    def set_workspace_status(
        self,
        workspace_id: str,
        status: str,
    ) -> WorkspaceRecord:
        normalized_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_status = (
            normalize_workspace_status(
                status
            )
        )

        session = self._session_factory()

        try:
            workspace = self._load_workspace(
                session,
                normalized_id,
            )

            workspace.status = (
                normalized_status
            )

            workspace.updated_at = (
                utc_now()
            )

            session.add(
                workspace
            )

            session.commit()
            session.refresh(
                workspace
            )

            return _workspace_record(
                workspace
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            session.rollback()

            raise WorkspacePersistenceError(
                "Workspace status update failed."
            ) from exc

        finally:
            session.close()

    def add_membership(
        self,
        *,
        workspace_id: str,
        user_id: str | int,
        status: str = "active",
        is_default: bool = False,
    ) -> WorkspaceMembershipRecord:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        normalized_status = (
            normalize_membership_status(
                status
            )
        )

        if (
            is_default
            and normalized_status
            != "active"
        ):
            raise InvalidMembershipStatusError(
                "A default membership must be active."
            )

        session = self._session_factory()

        try:
            self._load_workspace(
                session,
                normalized_workspace_id,
            )

            self._load_account(
                session,
                normalized_user_id,
            )

            existing = session.exec(
                select(
                    WorkspaceMembership
                ).where(
                    WorkspaceMembership.workspace_id
                    == normalized_workspace_id,
                    WorkspaceMembership.user_id
                    == normalized_user_id,
                )
            ).first()

            if existing is not None:
                raise WorkspaceMembershipConflictError(
                    "Workspace membership already exists."
                )

            if is_default:
                current_memberships = session.exec(
                    select(
                        WorkspaceMembership
                    ).where(
                        WorkspaceMembership.user_id
                        == normalized_user_id
                    )
                ).all()

                now = utc_now()

                for current in current_memberships:
                    if current.is_default:
                        current.is_default = False
                        current.updated_at = now
                        session.add(
                            current
                        )

            now = utc_now()

            membership = WorkspaceMembership(
                workspace_id=(
                    normalized_workspace_id
                ),
                user_id=normalized_user_id,
                status=normalized_status,
                is_default=bool(
                    is_default
                ),
                created_at=now,
                updated_at=now,
            )

            session.add(
                membership
            )

            try:
                session.commit()
                session.refresh(
                    membership
                )

            except IntegrityError as exc:
                session.rollback()

                raise (
                    WorkspaceMembershipConflictError(
                        "Workspace membership conflicts "
                        "with an existing record."
                    )
                ) from exc

            return _membership_record(
                membership
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            session.rollback()

            raise WorkspacePersistenceError(
                "Workspace membership creation failed."
            ) from exc

        finally:
            session.close()

    def list_user_memberships(
        self,
        user_id: str | int,
        *,
        active_only: bool = False,
    ) -> tuple[
        WorkspaceMembershipRecord,
        ...,
    ]:
        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        session = self._session_factory()

        try:
            self._load_account(
                session,
                normalized_user_id,
            )

            statement = select(
                WorkspaceMembership
            ).where(
                WorkspaceMembership.user_id
                == normalized_user_id
            )

            if active_only:
                statement = statement.where(
                    WorkspaceMembership.status
                    == "active"
                )

            statement = statement.order_by(
                WorkspaceMembership.workspace_id
            )

            memberships = session.exec(
                statement
            ).all()

            return tuple(
                _membership_record(
                    membership
                )
                for membership in memberships
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            raise WorkspacePersistenceError(
                "Workspace membership listing failed."
            ) from exc

        finally:
            session.close()

    def set_membership_status(
        self,
        *,
        workspace_id: str,
        user_id: str | int,
        status: str,
    ) -> WorkspaceMembershipRecord:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        normalized_status = (
            normalize_membership_status(
                status
            )
        )

        session = self._session_factory()

        try:
            membership = self._load_membership(
                session,
                workspace_id=(
                    normalized_workspace_id
                ),
                user_id=normalized_user_id,
            )

            membership.status = (
                normalized_status
            )

            membership.updated_at = (
                utc_now()
            )

            session.add(
                membership
            )

            session.commit()
            session.refresh(
                membership
            )

            return _membership_record(
                membership
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            session.rollback()

            raise WorkspacePersistenceError(
                "Workspace membership status update failed."
            ) from exc

        finally:
            session.close()

    def set_default_membership(
        self,
        *,
        workspace_id: str,
        user_id: str | int,
    ) -> WorkspaceMembershipRecord:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        session = self._session_factory()

        try:
            workspace = self._load_workspace(
                session,
                normalized_workspace_id,
            )

            if workspace.status != "active":
                raise WorkspaceInactiveError(
                    "Workspace is not active."
                )

            selected = self._load_membership(
                session,
                workspace_id=(
                    normalized_workspace_id
                ),
                user_id=normalized_user_id,
            )

            if selected.status != "active":
                raise WorkspaceMembershipInactiveError(
                    "Workspace membership is not active."
                )

            memberships = session.exec(
                select(
                    WorkspaceMembership
                ).where(
                    WorkspaceMembership.user_id
                    == normalized_user_id
                )
            ).all()

            now = utc_now()

            for membership in memberships:
                membership.is_default = (
                    membership.id
                    == selected.id
                )

                membership.updated_at = now

                session.add(
                    membership
                )

            session.commit()
            session.refresh(
                selected
            )

            return _membership_record(
                selected
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            session.rollback()

            raise WorkspacePersistenceError(
                "Default workspace update failed."
            ) from exc

        finally:
            session.close()

    def require_active_membership(
        self,
        *,
        workspace_id: str,
        user_id: str | int,
    ) -> ActiveWorkspaceMembership:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )

        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        session = self._session_factory()

        try:
            workspace = self._load_workspace(
                session,
                normalized_workspace_id,
            )

            if workspace.status != "active":
                raise WorkspaceInactiveError(
                    "Workspace is not active."
                )

            membership = self._load_membership(
                session,
                workspace_id=(
                    normalized_workspace_id
                ),
                user_id=normalized_user_id,
            )

            if membership.status != "active":
                raise WorkspaceMembershipInactiveError(
                    "Workspace membership is not active."
                )

            return ActiveWorkspaceMembership(
                workspace=_workspace_record(
                    workspace
                ),
                membership=_membership_record(
                    membership
                ),
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            raise WorkspacePersistenceError(
                "Active workspace membership "
                "resolution failed."
            ) from exc

        finally:
            session.close()

    def resolve_default_membership(
        self,
        user_id: str | int,
    ) -> ActiveWorkspaceMembership:
        normalized_user_id = (
            normalize_workspace_user_id(
                user_id
            )
        )

        session = self._session_factory()

        try:
            self._load_account(
                session,
                normalized_user_id,
            )

            memberships = session.exec(
                select(
                    WorkspaceMembership
                ).where(
                    WorkspaceMembership.user_id
                    == normalized_user_id,
                    WorkspaceMembership.is_default
                    .is_(True),
                )
            ).all()

            if len(memberships) != 1:
                raise DefaultWorkspaceResolutionError(
                    "Exactly one default workspace "
                    "membership is required."
                )

            membership = memberships[0]

            if membership.status != "active":
                raise WorkspaceMembershipInactiveError(
                    "Default workspace membership "
                    "is not active."
                )

            workspace = self._load_workspace(
                session,
                membership.workspace_id,
            )

            if workspace.status != "active":
                raise WorkspaceInactiveError(
                    "Default workspace is not active."
                )

            return ActiveWorkspaceMembership(
                workspace=_workspace_record(
                    workspace
                ),
                membership=_membership_record(
                    membership
                ),
            )

        except WorkspaceRepositoryError:
            raise

        except SQLAlchemyError as exc:
            raise WorkspacePersistenceError(
                "Default workspace resolution failed."
            ) from exc

        finally:
            session.close()


def get_workspace_repository() -> WorkspaceRepository:
    return WorkspaceRepository()
