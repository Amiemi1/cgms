from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.models.security_models import (
    BrowserSessionRecord,
)
from app.db.session import SessionLocal
from app.services.auth.account_authorization import (
    normalize_account_identifier,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
)
from app.services.security.canonical_roles import (
    CanonicalRoleResolutionError,
    canonical_role_name,
)
from app.services.workspace.repository import (
    InvalidWorkspaceIdentifierError,
    normalize_workspace_identifier,
)


session_registry_logger = logging.getLogger(
    "cgms.security.session_registry"
)

_REVOCATION_REASON_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9_.-]{0,63}$"
)


class BrowserSessionRegistryError(
    RuntimeError
):
    """
    Base error for persistent browser-session state failures.
    """


class BrowserSessionNotRegisteredError(
    BrowserSessionRegistryError
):
    """
    Raised when a signed session has no corresponding
    server-side session record.
    """


class BrowserSessionRevokedError(
    BrowserSessionRegistryError
):
    """
    Raised when a browser session has been revoked.
    """


class BrowserSessionExpiredError(
    BrowserSessionRegistryError
):
    """
    Raised when a browser-session record is expired.
    """


class BrowserSessionRecordMismatchError(
    BrowserSessionRegistryError
):
    """
    Raised when a persisted record does not match the signed
    browser-session identity.
    """


class BrowserSessionRecordConflictError(
    BrowserSessionRegistryError
):
    """
    Raised when a token ID is already registered with
    conflicting or revoked state.
    """


class BrowserSessionRevocationReasonError(
    BrowserSessionRegistryError
):
    """
    Raised when a revocation reason does not use the controlled
    machine-readable format.
    """


class BrowserSessionWorkspaceError(
    BrowserSessionRegistryError
):
    """
    Raised when a browser session cannot be bound to a valid
    workspace identifier.
    """

@dataclass(
    frozen=True,
    slots=True,
)
class BrowserSessionState:
    token_id: str
    user_id: int
    workspace_id: str

    role: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revoked_by_user_id: int | None
    revocation_reason: str | None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired_at(
        self,
        current_time: datetime,
    ) -> bool:
        return (
            self.expires_at
            <= _as_utc(current_time)
        )

    def is_active_at(
        self,
        current_time: datetime,
    ) -> bool:
        return (
            not self.is_revoked
            and not self.is_expired_at(
                current_time
            )
        )


def _as_utc(
    value: datetime,
) -> datetime:
    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def _current_time(
    supplied_time: datetime | None,
) -> datetime:
    return _as_utc(
        supplied_time
        if supplied_time is not None
        else datetime.now(timezone.utc)
    )


def _normalize_token_id(
    token_id: str,
) -> str:
    if not isinstance(token_id, str):
        raise BrowserSessionRecordMismatchError(
            "Browser session record does not match."
        )

    normalized = token_id.strip()

    if (
        not normalized
        or len(normalized) > 64
    ):
        raise BrowserSessionRecordMismatchError(
            "Browser session record does not match."
        )

    return normalized


def _normalize_revocation_reason(
    reason: str,
) -> str:
    if not isinstance(reason, str):
        raise BrowserSessionRevocationReasonError(
            "Invalid session revocation reason."
        )

    normalized = reason.strip().lower()

    if not _REVOCATION_REASON_PATTERN.fullmatch(
        normalized
    ):
        raise BrowserSessionRevocationReasonError(
            "Invalid session revocation reason."
        )

    return normalized


def _normalize_role(
    role: str,
) -> str:
    try:
        return canonical_role_name(role)
    except CanonicalRoleResolutionError as exc:
        raise BrowserSessionRecordMismatchError(
            "Browser session record does not match."
        ) from exc


def _normalize_workspace_id(
    value: str,
) -> str:
    try:
        return normalize_workspace_identifier(
            value
        )

    except InvalidWorkspaceIdentifierError as exc:
        raise BrowserSessionWorkspaceError(
            "Browser session workspace is invalid."
        ) from exc

def _state_from_record(
    record: BrowserSessionRecord,
) -> BrowserSessionState:
    return BrowserSessionState(
        token_id=record.token_id,
        user_id=record.user_id,
        workspace_id=_normalize_workspace_id(
            record.workspace_id
        ),
        role=_normalize_role(
            record.role
        ),
        issued_at=_as_utc(
            record.issued_at
        ),
        expires_at=_as_utc(
            record.expires_at
        ),
        revoked_at=(
            _as_utc(record.revoked_at)
            if record.revoked_at is not None
            else None
        ),
        revoked_by_user_id=(
            record.revoked_by_user_id
        ),
        revocation_reason=(
            record.revocation_reason
        ),
    )


def _record_matches_identity(
    record: BrowserSessionRecord,
    identity: BrowserSessionIdentity,
) -> bool:
    try:
        record_user_id = (
            normalize_account_identifier(
                record.user_id
            )
        )

        identity_user_id = (
            normalize_account_identifier(
                identity.user_id
            )
        )

        record_role = _normalize_role(
            record.role
        )

        identity_role = _normalize_role(
            identity.role
        )

    except (
        BrowserSessionRecordMismatchError,
        ValueError,
    ):
        return False

    return (
        record.token_id
        == _normalize_token_id(
            identity.token_id
        )
        and record_user_id
        == identity_user_id
        and record_role
        == identity_role
        and _as_utc(record.issued_at)
        == _as_utc(identity.issued_at)
        and _as_utc(record.expires_at)
        == _as_utc(identity.expires_at)
    )


class BrowserSessionRegistry:
    """
    Persistent allowlist for browser sessions.

    Only the JWT identifier and authoritative metadata are
    persisted. The raw JWT and cookie value are never stored.
    """

    def __init__(
        self,
        session_factory: Callable[
            [],
            Session,
        ] = SessionLocal,
    ) -> None:
        self._session_factory = (
            session_factory
        )

    def register(
        self,
        identity: BrowserSessionIdentity,
        *,
        workspace_id: str,
        now: datetime | None = None,
    ) -> BrowserSessionState:
        current_time = _current_time(now)

        normalized_workspace_id = (
            _normalize_workspace_id(
                workspace_id
            )
        )

        token_id = _normalize_token_id(
            identity.token_id
        )

        user_id = (
            normalize_account_identifier(
                identity.user_id
            )
        )

        role = _normalize_role(
            identity.role
        )

        issued_at = _as_utc(
            identity.issued_at
        )

        expires_at = _as_utc(
            identity.expires_at
        )

        if expires_at <= current_time:
            raise BrowserSessionExpiredError(
                "Browser session is expired."
            )

        if expires_at <= issued_at:
            raise BrowserSessionRecordMismatchError(
                "Browser session record does not match."
            )

        session = self._session_factory()

        try:
            existing = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.token_id
                    == token_id
                )
            ).first()

            if existing is not None:
                if (
                    not _record_matches_identity(
                        existing,
                        identity,
                    )
                    or _normalize_workspace_id(
                        existing.workspace_id
                    )
                    != normalized_workspace_id
                ):
                    raise (
                        BrowserSessionRecordConflictError(
                            "Browser session token ID "
                            "is already registered."
                        )
                    )

                state = _state_from_record(
                    existing
                )

                if state.is_revoked:
                    raise (
                        BrowserSessionRecordConflictError(
                            "Revoked browser session "
                            "cannot be registered again."
                        )
                    )

                return state

            record = BrowserSessionRecord(
                token_id=token_id,
                user_id=user_id,
                workspace_id=(
                    normalized_workspace_id
                ),
                role=role,
                issued_at=issued_at,
                expires_at=expires_at,
            )

            session.add(record)

            try:
                session.commit()
                session.refresh(record)

            except IntegrityError as exc:
                session.rollback()

                concurrent_record = session.exec(
                    select(
                        BrowserSessionRecord
                    ).where(
                        BrowserSessionRecord.token_id
                        == token_id
                    )
                ).first()

                if (
                    concurrent_record is not None
                    and _record_matches_identity(
                        concurrent_record,
                        identity,
                    )
                    and _normalize_workspace_id(
                        concurrent_record.workspace_id
                    )
                    == normalized_workspace_id
                    and concurrent_record.revoked_at
                    is None
                ):
                    return _state_from_record(
                        concurrent_record
                    )

                raise (
                    BrowserSessionRecordConflictError(
                        "Browser session token ID "
                        "is already registered."
                    )
                ) from exc

            state = _state_from_record(
                record
            )

            session_registry_logger.info(
                "browser_session_registered "
                "user_id=%s role=%s token_id=%s "
                "expires_at=%s",
                state.user_id,
                state.role,
                state.token_id,
                state.expires_at.isoformat(),
            )

            return state

        finally:
            session.close()

    def set_workspace(
        self,
        identity: BrowserSessionIdentity,
        *,
        workspace_id: str,
        now: datetime | None = None,
    ) -> BrowserSessionState:
        """
        Bind one active persistent browser session to a workspace.

        Membership and workspace lifecycle validation is performed
        by the authoritative workspace resolver before this method
        is called. The update is restricted to the selected token ID.
        """
        current_time = _current_time(now)

        normalized_workspace_id = (
            _normalize_workspace_id(
                workspace_id
            )
        )

        token_id = _normalize_token_id(
            identity.token_id
        )

        session = self._session_factory()

        try:
            record = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.token_id
                    == token_id
                )
            ).first()

            if record is None:
                raise BrowserSessionNotRegisteredError(
                    "Browser session is not registered."
                )

            if not _record_matches_identity(
                record,
                identity,
            ):
                raise BrowserSessionRecordMismatchError(
                    "Browser session record does not match."
                )

            state = _state_from_record(
                record
            )

            if state.is_revoked:
                raise BrowserSessionRevokedError(
                    "Browser session is revoked."
                )

            if state.is_expired_at(
                current_time
            ):
                raise BrowserSessionExpiredError(
                    "Browser session is expired."
                )

            if (
                state.workspace_id
                != normalized_workspace_id
            ):
                record.workspace_id = (
                    normalized_workspace_id
                )

                session.add(
                    record
                )

                session.commit()
                session.refresh(
                    record
                )

                state = _state_from_record(
                    record
                )

            session_registry_logger.info(
                "browser_session_workspace_bound "
                "user_id=%s workspace_id=%s token_id=%s",
                state.user_id,
                state.workspace_id,
                state.token_id,
            )

            return state

        finally:
            session.close()

    def require_active(
        self,
        identity: BrowserSessionIdentity,
        *,
        now: datetime | None = None,
    ) -> BrowserSessionState:
        current_time = _current_time(now)

        token_id = _normalize_token_id(
            identity.token_id
        )

        session = self._session_factory()

        try:
            record = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.token_id
                    == token_id
                )
            ).first()

            if record is None:
                raise (
                    BrowserSessionNotRegisteredError(
                        "Browser session is not registered."
                    )
                )

            if not _record_matches_identity(
                record,
                identity,
            ):
                raise (
                    BrowserSessionRecordMismatchError(
                        "Browser session record "
                        "does not match."
                    )
                )

            state = _state_from_record(
                record
            )

            if state.is_revoked:
                raise BrowserSessionRevokedError(
                    "Browser session is revoked."
                )

            if state.is_expired_at(
                current_time
            ):
                raise BrowserSessionExpiredError(
                    "Browser session is expired."
                )

            return state

        finally:
            session.close()

    def revoke(
        self,
        identity: BrowserSessionIdentity,
        *,
        reason: str = "logout",
        revoked_by_user_id: (
            str | int | None
        ) = None,
        now: datetime | None = None,
    ) -> BrowserSessionState:
        current_time = _current_time(now)

        token_id = _normalize_token_id(
            identity.token_id
        )

        normalized_reason = (
            _normalize_revocation_reason(
                reason
            )
        )

        normalized_revoker = (
            normalize_account_identifier(
                revoked_by_user_id
            )
            if revoked_by_user_id is not None
            else None
        )

        session = self._session_factory()

        try:
            record = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.token_id
                    == token_id
                )
            ).first()

            if record is None:
                raise (
                    BrowserSessionNotRegisteredError(
                        "Browser session is not registered."
                    )
                )

            if not _record_matches_identity(
                record,
                identity,
            ):
                raise (
                    BrowserSessionRecordMismatchError(
                        "Browser session record "
                        "does not match."
                    )
                )

            if record.revoked_at is None:
                record.revoked_at = current_time
                record.revocation_reason = (
                    normalized_reason
                )
                record.revoked_by_user_id = (
                    normalized_revoker
                )

                session.add(record)
                session.commit()
                session.refresh(record)

            state = _state_from_record(
                record
            )

            session_registry_logger.info(
                "browser_session_revoked "
                "user_id=%s token_id=%s reason=%s "
                "revoked_by_user_id=%s",
                state.user_id,
                state.token_id,
                state.revocation_reason,
                (
                    state.revoked_by_user_id
                    if state.revoked_by_user_id
                    is not None
                    else "self"
                ),
            )

            return state

        finally:
            session.close()

    def revoke_all_for_user(
        self,
        user_id: str | int,
        *,
        reason: str = "account_revocation",
        revoked_by_user_id: (
            str | int | None
        ) = None,
        now: datetime | None = None,
    ) -> int:
        normalized_user_id = (
            normalize_account_identifier(
                user_id
            )
        )

        normalized_reason = (
            _normalize_revocation_reason(
                reason
            )
        )

        normalized_revoker = (
            normalize_account_identifier(
                revoked_by_user_id
            )
            if revoked_by_user_id is not None
            else None
        )

        current_time = _current_time(now)

        session = self._session_factory()

        try:
            records = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.user_id
                    == normalized_user_id,
                    BrowserSessionRecord.revoked_at
                    .is_(None),
                )
            ).all()

            revoked_count = 0

            for record in records:
                if (
                    _as_utc(record.expires_at)
                    <= current_time
                ):
                    continue

                record.revoked_at = current_time
                record.revocation_reason = (
                    normalized_reason
                )
                record.revoked_by_user_id = (
                    normalized_revoker
                )

                session.add(record)
                revoked_count += 1

            if revoked_count:
                session.commit()

            session_registry_logger.info(
                "browser_sessions_revoked_for_user "
                "user_id=%s count=%s reason=%s "
                "revoked_by_user_id=%s",
                normalized_user_id,
                revoked_count,
                normalized_reason,
                (
                    normalized_revoker
                    if normalized_revoker
                    is not None
                    else "self"
                ),
            )

            return revoked_count

        finally:
            session.close()