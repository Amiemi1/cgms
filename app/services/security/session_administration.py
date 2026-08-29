from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.db.models.security_models import (
    BrowserSessionRecord,
    SecurityLog,
)
from app.db.session import SessionLocal
from app.services.auth.account_authorization import (
    InvalidAccountIdentifierError,
    normalize_account_identifier,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.security.rbac_policy import (
    MANAGE_BROWSER_SESSIONS,
)
from app.services.persistence.audit_store import (
    SECURITY_AUDIT,
    add_audit_record,
)


session_administration_logger = logging.getLogger(
    "cgms.security.session_administration"
)

ADMIN_SESSION_REVOCATION_ACTION = (
    "browser_sessions_admin_revoked"
)

DEFAULT_ADMIN_REVOCATION_REASON = (
    "admin_revocation"
)

_REVOCATION_REASON_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9_.-]{0,63}$"
)


class SessionAdministrationError(
    RuntimeError
):
    """
    Base error for administrative browser-session operations.
    """


class SessionAdministrationPermissionError(
    SessionAdministrationError
):
    """
    Raised when the authenticated actor lacks the required
    administrative permission.
    """


class SessionAdministrationInputError(
    SessionAdministrationError
):
    """
    Raised when an actor, target or revocation reason is
    invalid.
    """


class SessionAdministrationPersistenceError(
    SessionAdministrationError
):
    """
    Raised when revocation and audit persistence cannot be
    committed atomically.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class AdministrativeSessionRevocationResult:
    actor_user_id: int
    target_user_id: int
    revoked_count: int
    reason: str
    revoked_at: datetime

    @property
    def sessions_were_revoked(
        self,
    ) -> bool:
        return self.revoked_count > 0


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
    if supplied_time is None:
        return datetime.now(
            timezone.utc
        )

    return _as_utc(
        supplied_time
    )


def _normalize_user_id(
    value: str | int,
    *,
    field_name: str,
) -> int:
    try:
        return normalize_account_identifier(
            value
        )

    except InvalidAccountIdentifierError as exc:
        raise SessionAdministrationInputError(
            f"Invalid {field_name}."
        ) from exc


def _normalize_reason(
    reason: str,
) -> str:
    if not isinstance(reason, str):
        raise SessionAdministrationInputError(
            "Invalid session revocation reason."
        )

    normalized = (
        reason.strip().lower()
    )

    if not _REVOCATION_REASON_PATTERN.fullmatch(
        normalized
    ):
        raise SessionAdministrationInputError(
            "Invalid session revocation reason."
        )

    return normalized


def _build_audit_details(
    *,
    actor_user_id: int,
    target_user_id: int,
    revoked_count: int,
    reason: str,
) -> str:
    """
    Produce deterministic, machine-readable audit metadata.

    No JWT, cookie, password, email address or secret is
    included.
    """
    return json.dumps(
        {
            "actor_user_id": actor_user_id,
            "reason": reason,
            "revoked_count": revoked_count,
            "target_user_id": target_user_id,
        },
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )


class SessionAdministrationService:
    """
    Perform privileged browser-session administration.

    Session updates and the corresponding SecurityLog entry are
    persisted within one database transaction.
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

    def revoke_user_sessions(
        self,
        *,
        actor: AuthenticatedPrincipal,
        target_user_id: str | int,
        reason: str = (
            DEFAULT_ADMIN_REVOCATION_REASON
        ),
        now: datetime | None = None,
    ) -> AdministrativeSessionRevocationResult:
        if not actor.has_permission(
            MANAGE_BROWSER_SESSIONS
        ):
            session_administration_logger.warning(
                "admin_session_revocation_denied "
                "actor_user_id=%s role=%s "
                "reason=permission_denied",
                actor.user_id,
                actor.role,
            )

            raise (
                SessionAdministrationPermissionError(
                    "Administrative session permission "
                    "is required."
                )
            )

        actor_user_id = _normalize_user_id(
            actor.user_id,
            field_name="actor user identifier",
        )

        normalized_target_user_id = (
            _normalize_user_id(
                target_user_id,
                field_name=(
                    "target user identifier"
                ),
            )
        )

        normalized_reason = (
            _normalize_reason(
                reason
            )
        )

        revoked_at = _current_time(
            now
        )

        session = self._session_factory()

        try:
            records = session.exec(
                select(
                    BrowserSessionRecord
                ).where(
                    BrowserSessionRecord.user_id
                    == normalized_target_user_id,
                    BrowserSessionRecord.revoked_at
                    .is_(None),
                )
            ).all()

            revoked_count = 0

            for record in records:
                record_expiry = _as_utc(
                    record.expires_at
                )

                if record_expiry <= revoked_at:
                    continue

                record.revoked_at = revoked_at

                record.revoked_by_user_id = (
                    actor_user_id
                )

                record.revocation_reason = (
                    normalized_reason
                )

                session.add(
                    record
                )

                revoked_count += 1

            audit_details = (
                _build_audit_details(
                    actor_user_id=(
                        actor_user_id
                    ),
                    target_user_id=(
                        normalized_target_user_id
                    ),
                    revoked_count=(
                        revoked_count
                    ),
                    reason=(
                        normalized_reason
                    ),
                )
            )

            security_log = SecurityLog(
                user_id=actor_user_id,
                workspace_id=(
                    actor.workspace_id
                ),
                action=(
                    ADMIN_SESSION_REVOCATION_ACTION
                ),
                details=audit_details,
                created_at=revoked_at,
            )
            session.add(
                security_log
            )
            session.flush()
            add_audit_record(
                session,
                category=SECURITY_AUDIT,
                action=(
                    ADMIN_SESSION_REVOCATION_ACTION
                ),
                source="session_administration",
                workspace_id=(
                    actor.workspace_id
                ),
                actor_id=actor_user_id,
                subject_type="account_sessions",
                subject_id=(
                    normalized_target_user_id
                ),
                outcome="revoked",
                details=json.loads(
                    audit_details
                ),
                occurred_at=revoked_at,
                origin_id=(
                    "legacy.security_log:"
                    f"{security_log.id}"
                ),
            )

            session.commit()

            result = (
                AdministrativeSessionRevocationResult(
                    actor_user_id=(
                        actor_user_id
                    ),
                    target_user_id=(
                        normalized_target_user_id
                    ),
                    revoked_count=(
                        revoked_count
                    ),
                    reason=(
                        normalized_reason
                    ),
                    revoked_at=(
                        revoked_at
                    ),
                )
            )

            session_administration_logger.info(
                "admin_session_revocation_completed "
                "actor_user_id=%s target_user_id=%s "
                "revoked_count=%s reason=%s",
                result.actor_user_id,
                result.target_user_id,
                result.revoked_count,
                result.reason,
            )

            return result

        except SessionAdministrationError:
            session.rollback()
            raise

        except Exception as exc:
            session.rollback()

            session_administration_logger.exception(
                "admin_session_revocation_failed "
                "actor_user_id=%s target_user_id=%s "
                "reason=persistence_failure",
                actor_user_id,
                normalized_target_user_id,
            )

            raise (
                SessionAdministrationPersistenceError(
                    "Administrative session revocation "
                    "could not be persisted."
                )
            ) from exc

        finally:
            session.close()
