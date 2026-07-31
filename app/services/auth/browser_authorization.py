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
from app.services.workspace.repository import (
    WorkspaceRepositoryError,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
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
    workspace_id: str,
    service: AccountAuthorizationService,
    workspace_context_resolver: (
        WorkspaceContextResolver
    ),
) -> AuthenticatedPrincipal:
    """
    Revalidate a browser session against current account, role,
    workspace membership and workspace lifecycle state.

    Workspace identity is supplied from the persistent browser
    session record and is never accepted from the browser JWT.
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

    token_user_id = (
        identity.user_id.strip()
    )

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

    try:
        workspace_context = (
            workspace_context_resolver
            .resolve_requested(
                user_id=authorization.user_id,
                workspace_id=workspace_id,
            )
        )

    except WorkspaceRepositoryError as exc:
        raise _deny(
            reason="workspace_not_authorized",
            identity=identity,
        ) from exc

    principal = AuthenticatedPrincipal(
        user_id=authorization.token_subject,
        workspace_id=(
            workspace_context.workspace_id
        ),
        role=authorization.canonical_role,
        permissions=authorization.permissions,
        token_id=identity.token_id,
    )

    browser_authorization_logger.info(
        "browser_session_revalidation_granted "
        "user_id=%s workspace_id=%s "
        "role=%s token_id=%s",
        principal.user_id,
        principal.workspace_id,
        principal.role,
        principal.token_id
        or "not-recorded",
    )

    return principal
