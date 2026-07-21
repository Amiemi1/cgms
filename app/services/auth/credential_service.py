from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import func
from sqlmodel import Session, select

from app.db.models.security_models import UserRole
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.auth.account_authorization import (
    AccountRoleConfigurationError,
    resolve_account_role_records,
)
from app.services.auth.security import (
    hash_password,
    verify_password,
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
    Role assignments are resolved through the same authoritative
    fail-closed resolver used for request-time authorization.
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

            account = AuthenticatedAccount(
                user_id=user.id,
                email=normalized_email,
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
            )

            credential_logger.info(
                "credential_authentication_granted "
                "user_id=%s role=%s legacy_alias=%s",
                account.user_id,
                account.canonical_role,
                account.used_legacy_alias,
            )

            return account

        except AccountRoleConfigurationError:
            credential_logger.error(
                "credential_authentication_denied "
                "user_id=%s "
                "reason=invalid_role_configuration",
                (
                    user.id
                    if user is not None
                    and user.id is not None
                    else "not-recorded"
                ),
            )

            raise

        finally:
            session.close()


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