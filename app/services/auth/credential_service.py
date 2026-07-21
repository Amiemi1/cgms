from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import func
from sqlmodel import Session, select

from app.db.models.security_models import UserRole
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.auth.security import (
    hash_password,
    verify_password,
)
from app.services.security.canonical_roles import (
    CANONICAL_VIEWER,
    CanonicalRoleResolution,
    CanonicalRoleResolutionError,
    resolve_canonical_role,
)


credential_logger = logging.getLogger(
    "cgms.security.credentials"
)

# Used only to reduce timing differences when an account does
# not exist. It is not a real account credential.
_DUMMY_PASSWORD_HASH = hash_password(
    "cgms-dummy-credential-verification-value"
)


class InvalidCredentialsError(ValueError):
    """
    Raised when supplied credentials cannot be authenticated.

    The public error is deliberately generic to prevent account
    enumeration.
    """


class AccountRoleConfigurationError(RuntimeError):
    """
    Raised when stored role assignments are unknown or conflict.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class AuthenticatedAccount:
    user_id: int
    email: str
    stored_role: str
    canonical_role: str
    used_legacy_alias: bool

    @property
    def token_subject(
        self,
    ) -> str:
        return str(self.user_id)


def normalize_email(
    email: str,
) -> str:
    if not isinstance(email, str):
        raise InvalidCredentialsError(
            "Invalid email or password."
        )

    normalized = email.strip().casefold()

    if (
        not normalized
        or len(normalized) > 320
        or "@" not in normalized
    ):
        raise InvalidCredentialsError(
            "Invalid email or password."
        )

    return normalized


def _validate_password_input(
    password: str,
) -> str:
    if (
        not isinstance(password, str)
        or not password
        or len(password) > 4096
    ):
        raise InvalidCredentialsError(
            "Invalid email or password."
        )

    return password


def _verify_password_safely(
    password: str,
    password_hash: str,
) -> bool:
    try:
        return verify_password(
            password,
            password_hash,
        )
    except (
        TypeError,
        ValueError,
    ):
        credential_logger.error(
            "credential_verification_failed "
            "reason=invalid_password_hash"
        )

        return False


class CredentialAuthenticationService:
    """
    Authenticate a database-backed CGMS account.

    Passwords are verified against the existing bcrypt hashes.
    Stored roles are translated through the canonical-role
    compatibility boundary before any token or session is issued.
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

    def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> AuthenticatedAccount:
        normalized_email = normalize_email(
            email
        )

        validated_password = (
            _validate_password_input(
                password
            )
        )

        session = self._session_factory()

        try:
            user = session.exec(
                select(User).where(
                    func.lower(User.email)
                    == normalized_email
                )
            ).first()

            if user is None:
                # Consume a bcrypt verification operation so an
                # unknown account is less distinguishable from a
                # wrong-password attempt.
                _verify_password_safely(
                    validated_password,
                    _DUMMY_PASSWORD_HASH,
                )

                credential_logger.warning(
                    "credential_authentication_denied "
                    "reason=invalid_credentials"
                )

                raise InvalidCredentialsError(
                    "Invalid email or password."
                )

            if not _verify_password_safely(
                validated_password,
                user.password_hash,
            ):
                credential_logger.warning(
                    "credential_authentication_denied "
                    "user_id=%s "
                    "reason=invalid_credentials",
                    user.id or "not-recorded",
                )

                raise InvalidCredentialsError(
                    "Invalid email or password."
                )

            if user.id is None:
                credential_logger.error(
                    "credential_authentication_denied "
                    "reason=missing_user_id"
                )

                raise InvalidCredentialsError(
                    "Invalid email or password."
                )

            role_resolution = (
                self._resolve_user_role(
                    session=session,
                    user_id=user.id,
                )
            )

            account = AuthenticatedAccount(
                user_id=user.id,
                email=normalized_email,
                stored_role=(
                    role_resolution.supplied_role
                    or CANONICAL_VIEWER
                ),
                canonical_role=(
                    role_resolution.canonical_role
                ),
                used_legacy_alias=(
                    role_resolution
                    .used_legacy_alias
                ),
            )

            credential_logger.info(
                "credential_authentication_granted "
                "user_id=%s role=%s legacy_alias=%s",
                account.user_id,
                account.canonical_role,
                account.used_legacy_alias,
            )

            return account

        finally:
            session.close()

    def _resolve_user_role(
        self,
        *,
        session: Session,
        user_id: int,
    ) -> CanonicalRoleResolution:
        role_records = session.exec(
            select(UserRole).where(
                UserRole.user_id == user_id
            )
        ).all()

        if not role_records:
            return resolve_canonical_role(
                None,
                default_role=CANONICAL_VIEWER,
            )

        resolutions: list[
            CanonicalRoleResolution
        ] = []

        for role_record in role_records:
            try:
                resolution = (
                    resolve_canonical_role(
                        role_record.role
                    )
                )
            except CanonicalRoleResolutionError as exc:
                credential_logger.error(
                    "account_role_resolution_failed "
                    "user_id=%s reason=unknown_role",
                    user_id,
                )

                raise AccountRoleConfigurationError(
                    "Account role configuration is invalid."
                ) from exc

            resolutions.append(
                resolution
            )

        canonical_roles = {
            resolution.canonical_role
            for resolution in resolutions
        }

        if len(canonical_roles) != 1:
            credential_logger.error(
                "account_role_resolution_failed "
                "user_id=%s reason=conflicting_roles",
                user_id,
            )

            raise AccountRoleConfigurationError(
                "Account has conflicting role assignments."
            )

        # Prefer an exact canonical record over its legacy alias
        # when both resolve to the same canonical role.
        return sorted(
            resolutions,
            key=lambda resolution: (
                resolution.used_legacy_alias,
                resolution.normalized_role,
            ),
        )[0]


def authenticate_credentials(
    *,
    email: str,
    password: str,
) -> AuthenticatedAccount:
    return (
        CredentialAuthenticationService()
        .authenticate(
            email=email,
            password=password,
        )
    )