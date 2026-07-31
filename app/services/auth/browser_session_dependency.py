from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)

from app.services.auth.account_authorization import (
    AccountAuthorizationService,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_authorization import (
    BrowserSessionAuthorizationError,
    revalidate_browser_session,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
    decode_browser_session_token,
    get_browser_session_token,
)
from app.services.auth.session_registry import (
    BrowserSessionRegistry,
    BrowserSessionRegistryError,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
    get_workspace_context_resolver,
)


browser_authentication_logger = logging.getLogger(
    "cgms.security.browser_authentication"
)


def _browser_authentication_error(
    detail: str,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


def get_account_authorization_service(
) -> AccountAuthorizationService:
    """
    Provide the authoritative database-backed account and role
    resolver.

    Tests may override this dependency without changing the
    production authorization boundary.
    """
    return AccountAuthorizationService()


def get_browser_session_registry(
) -> BrowserSessionRegistry:
    """
    Provide the persistent server-side browser-session
    registry.

    Every protected browser request must match an active,
    non-expired and non-revoked registry record.
    """
    return BrowserSessionRegistry()


def get_current_browser_session_identity(
    request: Request,
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
) -> BrowserSessionIdentity:
    """
    Validate the host-bound browser-session cookie and its
    persistent server-side session record.

    Missing, malformed, expired, unregistered, revoked or
    mismatched sessions fail closed. Bearer tokens and
    caller-supplied role headers are not accepted as browser
    sessions.
    """
    token = get_browser_session_token(
        request
    )

    if token is None:
        browser_authentication_logger.warning(
            "browser_authentication_denied "
            "reason=missing_session"
        )

        raise _browser_authentication_error(
            "Browser session required."
        )

    identity = decode_browser_session_token(
        token
    )

    if identity is None:
        browser_authentication_logger.warning(
            "browser_authentication_denied "
            "reason=invalid_or_expired_session"
        )

        raise _browser_authentication_error(
            "Invalid or expired browser session."
        )

    try:
        session_state = (
            session_registry.require_active(
                identity
            )
        )

        request.state.cgms_browser_session_state = (
            session_state
        )

    except BrowserSessionRegistryError:
        browser_authentication_logger.warning(
            "browser_authentication_denied "
            "user_id=%s token_id=%s "
            "reason=session_not_active",
            identity.user_id,
            identity.token_id,
        )

        raise _browser_authentication_error(
            "Browser session is no longer active."
        )

    browser_authentication_logger.info(
        "browser_session_validated "
        "user_id=%s role=%s token_id=%s",
        identity.user_id,
        identity.role,
        identity.token_id,
    )

    return identity


def get_current_browser_principal(
    request: Request,
    identity: Annotated[
        BrowserSessionIdentity,
        Depends(
            get_current_browser_session_identity
        ),
    ],
    authorization_service: Annotated[
        AccountAuthorizationService,
        Depends(
            get_account_authorization_service
        ),
    ],
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
    workspace_context_resolver: Annotated[
        WorkspaceContextResolver,
        Depends(
            get_workspace_context_resolver
        ),
    ],
) -> AuthenticatedPrincipal:
    """
    Build a workspace-bound browser principal.

    The authoritative workspace comes from the persistent browser
    session registry. Account role, workspace membership and
    workspace lifecycle state are then revalidated.
    """
    try:
        session_state = getattr(
            request.state,
            "cgms_browser_session_state",
            None,
        )

        if session_state is None:
            session_state = (
                session_registry.require_active(
                    identity
                )
            )

        workspace_id = getattr(
            session_state,
            "workspace_id",
            None,
        )

        if (
            not isinstance(workspace_id, str)
            or not workspace_id.strip()
        ):
            raise BrowserSessionAuthorizationError(
                "invalid_session_workspace"
            )

        principal = revalidate_browser_session(
            identity=identity,
            workspace_id=workspace_id,
            service=authorization_service,
            workspace_context_resolver=(
                workspace_context_resolver
            ),
        )

    except (
        BrowserSessionAuthorizationError,
        BrowserSessionRegistryError,
    ):
        browser_authentication_logger.warning(
            "browser_authentication_denied "
            "user_id=%s token_id=%s "
            "reason=session_no_longer_authorized",
            identity.user_id,
            identity.token_id,
        )

        raise _browser_authentication_error(
            "Browser session is no longer authorized."
        )

    browser_authentication_logger.info(
        "browser_authentication_granted "
        "user_id=%s workspace_id=%s "
        "role=%s token_id=%s",
        principal.user_id,
        principal.workspace_id,
        principal.role,
        principal.token_id
        or "not-recorded",
    )

    return principal

def require_browser_permission(
    permission: str,
) -> Callable[..., AuthenticatedPrincipal]:
    """
    Require a permission from a database-revalidated browser
    principal whose persistent session is active.
    """
    normalized_permission = (
        permission.strip()
        if isinstance(permission, str)
        else ""
    )

    if not normalized_permission:
        raise ValueError(
            "A non-empty browser permission is required."
        )

    def checker(
        principal: Annotated[
            AuthenticatedPrincipal,
            Depends(
                get_current_browser_principal
            ),
        ],
    ) -> AuthenticatedPrincipal:
        if not principal.has_permission(
            normalized_permission
        ):
            browser_authentication_logger.warning(
                "browser_authorization_denied "
                "user_id=%s role=%s permission=%s "
                "token_id=%s",
                principal.user_id,
                principal.role,
                normalized_permission,
                principal.token_id
                or "not-recorded",
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Permission denied: "
                    f"{normalized_permission}"
                ),
                headers={
                    "Cache-Control": "no-store",
                    "Pragma": "no-cache",
                },
            )

        browser_authentication_logger.info(
            "browser_authorization_granted "
            "user_id=%s role=%s permission=%s "
            "token_id=%s",
            principal.user_id,
            principal.role,
            normalized_permission,
            principal.token_id
            or "not-recorded",
        )

        return principal

    return checker
