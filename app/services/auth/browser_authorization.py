from __future__ import annotations

import logging

from app.services.auth.account_authorization import (
    AccountAuthorizationError,
    AccountAuthorizationService,
    AccountNotFoundError,
    AccountRoleConfigurationError,
    InvalidAccountIdentifierError,
    ResolvedAccountAuthorization,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
)
from app.services.security.canonical_roles import (
    CanonicalRoleResolutionError,
    canonical_role_name,
)


browser_authorization_logger = logging.getLogger(
    "cgms.security.browser_authorization"
)


class BrowserSessionAuthorizationError(
    RuntimeError
):
    """
    Raised when a valid browser-session token no longer matches
    the current authoritative account state.

    The reason is intended for controlled internal logging and
    tests. It must not expose account details to the browser.
    """

    def __init__(
        self,
        reason: str,
    ) -> None:
        self.reason = reason

        super().__init__(
            "Browser session is no longer authorized."
        )


def _deny(
    *,
    reason: str,
    identity: BrowserSessionIdentity,
) -> BrowserSessionAuthorizationError:
    browser_authorization_logger.warning(
        "browser_session_revalidation_denied "
        "user_id=%s role=%s token_id=%s reason=%s",
        identity.user_id,
        identity.role,
        identity.token_id,
        reason,
    )

    return BrowserSessionAuthorizationError(
        reason
    )


def _resolve_current_authorization(
    *,
    identity: BrowserSessionIdentity,
    service: AccountAuthorizationService,
) -> ResolvedAccountAuthorization:
    try:
        return service.resolve(
            identity.user_id
        )

    except InvalidAccountIdentifierError as exc:
        raise _deny(
            reason="invalid_account_identifier",
            identity=identity,
        ) from exc

    except AccountNotFoundError as exc:
        raise _deny(
            reason="account_not_found",
            identity=identity,
        ) from exc

    except AccountRoleConfigurationError as exc:
        raise _deny(
            reason="invalid_role_configuration",
            identity=identity,
        ) from exc

    except AccountAuthorizationError as exc:
        raise _deny(
            reason="account_authorization_failed",
            identity=identity,
        ) from exc


def revalidate_browser_session(
    *,
    identity: BrowserSessionIdentity,
    service: AccountAuthorizationService,
) -> AuthenticatedPrincipal:
    """
    Revalidate a cryptographically valid browser session against
    the current database account and role state.

    Authorization succeeds only when:

    - the account still exists;
    - the persisted user identifier is canonical;
    - the account has one resolvable role;
    - the current canonical role matches the session role.

    A changed role requires a new login so that an old session
    cannot retain elevated permissions.
    """
    try:
        token_role = canonical_role_name(
            identity.role
        )
    except CanonicalRoleResolutionError as exc:
        raise _deny(
            reason="invalid_session_role",
            identity=identity,
        ) from exc

    authorization = (
        _resolve_current_authorization(
            identity=identity,
            service=service,
        )
    )

    token_user_id = identity.user_id.strip()

    if (
        authorization.token_subject
        != token_user_id
    ):
        raise _deny(
            reason="noncanonical_account_identifier",
            identity=identity,
        )

    if (
        authorization.canonical_role
        != token_role
    ):
        raise _deny(
            reason="role_changed",
            identity=identity,
        )

    principal = AuthenticatedPrincipal(
        user_id=authorization.token_subject,
        role=authorization.canonical_role,
        permissions=authorization.permissions,
        token_id=identity.token_id,
    )

    browser_authorization_logger.info(
        "browser_session_revalidation_granted "
        "user_id=%s role=%s token_id=%s",
        principal.user_id,
        principal.role,
        principal.token_id
        or "not-recorded",
    )

    return principal