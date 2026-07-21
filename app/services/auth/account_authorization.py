from __future__ import annotations

import logging
from collections.abc import (
    Callable,
    Collection,
)
from dataclasses import dataclass

from sqlmodel import Session, select

from app.db.models.security_models import UserRole
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.security.canonical_roles import (
    CanonicalRoleResolution,
    CanonicalRoleResolutionError,
    resolve_canonical_role,
)


account_authorization_logger = logging.getLogger(
    "cgms.security.account_authorization"
)


class AccountAuthorizationError(RuntimeError):
    """
    Base exception for authoritative account-resolution
    failures.
    """


class InvalidAccountIdentifierError(
    AccountAuthorizationError
):
    """
    Raised when a supplied account identifier cannot represent
    a valid persisted CGMS user.
    """


class AccountNotFoundError(
    AccountAuthorizationError
):
    """
    Raised when the authenticated account no longer exists.
    """


class AccountRoleConfigurationError(
    AccountAuthorizationError
):
    """
    Raised when an account has no role, an unknown role, or
    conflicting role assignments.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class ResolvedAccountAuthorization:
    user_id: int
    email: str
    stored_role: str
    canonical_role: str
    used_legacy_alias: bool
    permissions: frozenset[str]

    @property
    def token_subject(self) -> str:
        return str(self.user_id)


def normalize_account_identifier(
    user_id: str | int,
) -> int:
    """
    Convert a token subject into a valid positive database user
    identifier.

    Booleans are explicitly rejected because bool is a subclass
    of int in Python.
    """
    if isinstance(user_id, bool):
        raise InvalidAccountIdentifierError(
            "Invalid authenticated account."
        )

    if isinstance(user_id, int):
        normalized_user_id = user_id

    elif isinstance(user_id, str):
        candidate = user_id.strip()

        if (
            not candidate
            or not candidate.isdecimal()
        ):
            raise InvalidAccountIdentifierError(
                "Invalid authenticated account."
            )

        try:
            normalized_user_id = int(candidate)
        except ValueError as exc:
            raise InvalidAccountIdentifierError(
                "Invalid authenticated account."
            ) from exc

    else:
        raise InvalidAccountIdentifierError(
            "Invalid authenticated account."
        )

    if normalized_user_id <= 0:
        raise InvalidAccountIdentifierError(
            "Invalid authenticated account."
        )

    return normalized_user_id


def resolve_account_role_records(
    role_records: Collection[UserRole],
    *,
    user_id: int,
) -> CanonicalRoleResolution:
    """
    Resolve persisted role records into one canonical role.

    Missing roles fail closed. Multiple records are permitted
    only when every record maps to the same canonical role.
    """
    records = list(role_records)

    if not records:
        account_authorization_logger.error(
            "account_authorization_denied "
            "user_id=%s reason=missing_role",
            user_id,
        )

        raise AccountRoleConfigurationError(
            "Account role assignment is missing."
        )

    resolutions: list[
        CanonicalRoleResolution
    ] = []

    for role_record in records:
        try:
            resolution = resolve_canonical_role(
                role_record.role
            )
        except CanonicalRoleResolutionError as exc:
            account_authorization_logger.error(
                "account_authorization_denied "
                "user_id=%s reason=unknown_role",
                user_id,
            )

            raise AccountRoleConfigurationError(
                "Account role configuration is invalid."
            ) from exc

        resolutions.append(resolution)

    canonical_roles = {
        resolution.canonical_role
        for resolution in resolutions
    }

    if len(canonical_roles) != 1:
        account_authorization_logger.error(
            "account_authorization_denied "
            "user_id=%s reason=conflicting_roles",
            user_id,
        )

        raise AccountRoleConfigurationError(
            "Account has conflicting role assignments."
        )

    # Prefer an exact canonical record over a legacy alias when
    # both map to the same authorization role.
    return sorted(
        resolutions,
        key=lambda resolution: (
            resolution.used_legacy_alias,
            resolution.normalized_role,
        ),
    )[0]


class AccountAuthorizationService:
    """
    Resolve the current authoritative account and role state
    from the CGMS database.

    No user, role or permission value supplied by a browser
    cookie, request header or query parameter is trusted by this
    service.
    """

    def __init__(
        self,
        session_factory: Callable[
            [],
            Session,
        ] = SessionLocal,
    ) -> None:
        self._session_factory = session_factory

    def resolve(
        self,
        user_id: str | int,
    ) -> ResolvedAccountAuthorization:
        normalized_user_id = (
            normalize_account_identifier(
                user_id
            )
        )

        session = self._session_factory()

        try:
            user = session.exec(
                select(User).where(
                    User.id == normalized_user_id
                )
            ).first()

            if user is None:
                account_authorization_logger.warning(
                    "account_authorization_denied "
                    "user_id=%s reason=account_not_found",
                    normalized_user_id,
                )

                raise AccountNotFoundError(
                    "Authenticated account is unavailable."
                )

            if user.id is None:
                account_authorization_logger.error(
                    "account_authorization_denied "
                    "reason=missing_persisted_user_id"
                )

                raise AccountNotFoundError(
                    "Authenticated account is unavailable."
                )

            role_records = session.exec(
                select(UserRole).where(
                    UserRole.user_id == user.id
                )
            ).all()

            role_resolution = (
                resolve_account_role_records(
                    role_records,
                    user_id=user.id,
                )
            )

            authorization = (
                ResolvedAccountAuthorization(
                    user_id=user.id,
                    email=user.email,
                    stored_role=(
                        role_resolution.supplied_role
                    ),
                    canonical_role=(
                        role_resolution.canonical_role
                    ),
                    used_legacy_alias=(
                        role_resolution
                        .used_legacy_alias
                    ),
                    permissions=(
                        role_resolution.permissions
                    ),
                )
            )

            account_authorization_logger.info(
                "account_authorization_resolved "
                "user_id=%s role=%s legacy_alias=%s",
                authorization.user_id,
                authorization.canonical_role,
                authorization.used_legacy_alias,
            )

            return authorization

        finally:
            session.close()


def resolve_account_authorization(
    user_id: str | int,
) -> ResolvedAccountAuthorization:
    return AccountAuthorizationService().resolve(
        user_id
    )