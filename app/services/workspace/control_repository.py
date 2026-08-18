from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.db.models.user import User
from app.db.models.workspace import Workspace, utc_now
from app.db.models.workspace_control import (
    WorkspaceControl,
)
from app.db.session import SessionLocal
from app.services.workspace.repository import (
    WorkspaceNotFoundError,
    normalize_workspace_identifier,
    normalize_workspace_status,
    normalize_workspace_user_id,
)


class WorkspaceControlError(RuntimeError):
    """Base error for persistent workspace-control operations."""


class WorkspaceControlStateError(WorkspaceControlError):
    """Raised when a workspace lacks its required control record."""


class WorkspaceControlValidationError(WorkspaceControlError):
    """Raised when a workspace-control value is invalid."""


class WorkspaceControlPersistenceError(WorkspaceControlError):
    """Raised when a workspace-control transaction fails."""


@dataclass(frozen=True)
class WorkspaceAdminRecord:
    workspace_id: str
    suspended: bool
    suspension_reason: str | None
    updated_at: datetime


@dataclass(frozen=True)
class WorkspaceQuotaRecord:
    workspace_id: str
    max_events: int
    max_connectors: int
    max_users: int
    updated_by_user_id: int | None
    updated_at: datetime


def _normalize_suspension_reason(
    value: object,
) -> str:
    if not isinstance(value, str):
        raise WorkspaceControlValidationError(
            "Workspace suspension reason must be a string."
        )

    normalized = value.strip()

    if not normalized or len(normalized) > 500:
        raise WorkspaceControlValidationError(
            "Workspace suspension reason must contain 1 to 500 characters."
        )

    return normalized


def _normalize_quota_value(
    name: str,
    value: object,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise WorkspaceControlValidationError(
            f"{name} must be a non-negative integer."
        )

    if value < 0:
        raise WorkspaceControlValidationError(
            f"{name} must be a non-negative integer."
        )

    return value


def _admin_record(
    workspace: Workspace,
    control: WorkspaceControl,
) -> WorkspaceAdminRecord:
    return WorkspaceAdminRecord(
        workspace_id=workspace.id,
        suspended=workspace.status == "suspended",
        suspension_reason=(
            control.suspension_reason
            if workspace.status == "suspended"
            else None
        ),
        updated_at=max(
            workspace.updated_at,
            control.updated_at,
        ),
    )


def _quota_record(
    control: WorkspaceControl,
) -> WorkspaceQuotaRecord:
    return WorkspaceQuotaRecord(
        workspace_id=control.workspace_id,
        max_events=control.max_events,
        max_connectors=control.max_connectors,
        max_users=control.max_users,
        updated_by_user_id=control.updated_by_user_id,
        updated_at=control.updated_at,
    )


class WorkspaceControlRepository:
    """Persistent authority for workspace lifecycle metadata and quotas."""

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _load_workspace(
        session: Session,
        workspace_id: str,
    ) -> Workspace:
        workspace = session.exec(
            select(Workspace).where(
                Workspace.id == workspace_id
            )
        ).first()

        if workspace is None:
            raise WorkspaceNotFoundError(
                "Workspace does not exist."
            )

        return workspace

    @staticmethod
    def _load_control(
        session: Session,
        workspace_id: str,
    ) -> WorkspaceControl:
        control = session.exec(
            select(WorkspaceControl).where(
                WorkspaceControl.workspace_id
                == workspace_id
            )
        ).first()

        if control is None:
            raise WorkspaceControlStateError(
                "Workspace control record does not exist."
            )

        return control

    @staticmethod
    def _require_account(
        session: Session,
        user_id: int,
    ) -> None:
        account = session.exec(
            select(User.id).where(
                User.id == user_id
            )
        ).first()

        if account is None:
            raise WorkspaceControlValidationError(
                "Workspace control account does not exist."
            )

    def list_admin_state(
        self,
    ) -> tuple[WorkspaceAdminRecord, ...]:
        session = self._session_factory()

        try:
            rows = session.exec(
                select(
                    Workspace,
                    WorkspaceControl,
                ).join(
                    WorkspaceControl,
                    WorkspaceControl.workspace_id
                    == Workspace.id,
                ).order_by(
                    Workspace.id
                )
            ).all()

            return tuple(
                _admin_record(workspace, control)
                for workspace, control in rows
            )

        except WorkspaceControlError:
            raise

        except SQLAlchemyError as exc:
            raise WorkspaceControlPersistenceError(
                "Workspace administration listing failed."
            ) from exc

        finally:
            session.close()

    def set_workspace_lifecycle(
        self,
        workspace_id: str,
        status: str,
        *,
        suspension_reason: str | None = None,
        updated_by_user_id: str | int | None = None,
    ) -> WorkspaceAdminRecord:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )
        normalized_status = normalize_workspace_status(
            status
        )
        normalized_user_id = (
            normalize_workspace_user_id(
                updated_by_user_id
            )
            if updated_by_user_id is not None
            else None
        )

        if normalized_status == "suspended":
            normalized_reason = (
                _normalize_suspension_reason(
                    suspension_reason
                    if suspension_reason is not None
                    else "manual_admin_action"
                )
            )
        else:
            normalized_reason = None

        session = self._session_factory()

        try:
            workspace = self._load_workspace(
                session,
                normalized_workspace_id,
            )
            control = self._load_control(
                session,
                normalized_workspace_id,
            )

            if normalized_user_id is not None:
                self._require_account(
                    session,
                    normalized_user_id,
                )

            now = utc_now()
            workspace.status = normalized_status
            workspace.updated_at = now
            control.suspension_reason = normalized_reason
            control.updated_by_user_id = normalized_user_id
            control.updated_at = now

            session.add(workspace)
            session.add(control)
            session.commit()
            session.refresh(workspace)
            session.refresh(control)

            return _admin_record(
                workspace,
                control,
            )

        except (
            WorkspaceControlError,
            WorkspaceNotFoundError,
        ):
            session.rollback()
            raise

        except SQLAlchemyError as exc:
            session.rollback()
            raise WorkspaceControlPersistenceError(
                "Workspace lifecycle update failed."
            ) from exc

        finally:
            session.close()

    def list_quotas(
        self,
    ) -> tuple[WorkspaceQuotaRecord, ...]:
        session = self._session_factory()

        try:
            controls = session.exec(
                select(WorkspaceControl).order_by(
                    WorkspaceControl.workspace_id
                )
            ).all()

            return tuple(
                _quota_record(control)
                for control in controls
            )

        except SQLAlchemyError as exc:
            raise WorkspaceControlPersistenceError(
                "Workspace quota listing failed."
            ) from exc

        finally:
            session.close()

    def get_quota(
        self,
        workspace_id: str,
    ) -> WorkspaceQuotaRecord:
        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )
        session = self._session_factory()

        try:
            self._load_workspace(
                session,
                normalized_workspace_id,
            )
            control = self._load_control(
                session,
                normalized_workspace_id,
            )
            return _quota_record(control)

        except (
            WorkspaceControlError,
            WorkspaceNotFoundError,
        ):
            raise

        except SQLAlchemyError as exc:
            raise WorkspaceControlPersistenceError(
                "Workspace quota resolution failed."
            ) from exc

        finally:
            session.close()

    def set_quota(
        self,
        workspace_id: str,
        quota: dict[str, object],
        *,
        updated_by_user_id: str | int | None = None,
    ) -> WorkspaceQuotaRecord:
        if not isinstance(quota, dict):
            raise WorkspaceControlValidationError(
                "Workspace quota payload must be an object."
            )

        normalized_workspace_id = (
            normalize_workspace_identifier(
                workspace_id
            )
        )
        normalized_user_id = (
            normalize_workspace_user_id(
                updated_by_user_id
            )
            if updated_by_user_id is not None
            else None
        )

        field_map = {
            "maxEvents": "max_events",
            "maxConnectors": "max_connectors",
            "maxUsers": "max_users",
        }
        unknown_fields = set(quota) - set(field_map)

        if unknown_fields:
            raise WorkspaceControlValidationError(
                "Workspace quota payload contains unsupported fields."
            )

        values = {
            field_map[name]: _normalize_quota_value(
                name,
                value,
            )
            for name, value in quota.items()
        }

        session = self._session_factory()

        try:
            self._load_workspace(
                session,
                normalized_workspace_id,
            )
            control = self._load_control(
                session,
                normalized_workspace_id,
            )

            if normalized_user_id is not None:
                self._require_account(
                    session,
                    normalized_user_id,
                )

            for field_name, value in values.items():
                setattr(
                    control,
                    field_name,
                    value,
                )

            control.updated_by_user_id = normalized_user_id
            control.updated_at = utc_now()
            session.add(control)
            session.commit()
            session.refresh(control)

            return _quota_record(control)

        except (
            WorkspaceControlError,
            WorkspaceNotFoundError,
        ):
            session.rollback()
            raise

        except SQLAlchemyError as exc:
            session.rollback()
            raise WorkspaceControlPersistenceError(
                "Workspace quota update failed."
            ) from exc

        finally:
            session.close()


def get_workspace_control_repository(
) -> WorkspaceControlRepository:
    return WorkspaceControlRepository()
