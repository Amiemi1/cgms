from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.services.auth.jwt_handler import (
    decode_access_token,
)
from app.services.security.rbac_policy import (
    get_permissions,
    is_known_role,
    normalize_role,
)
from app.services.auth.account_authorization import (
    AccountAuthorizationError,
    AccountAuthorizationService,
)
from app.services.workspace.repository import (
    WorkspaceRepositoryError,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
    get_workspace_context_resolver,
)


security = HTTPBearer(
    auto_error=False
)

authentication_logger = logging.getLogger(
    "cgms.security.authentication"
)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """
    Server-validated identity used for CGMS authorization.

    Workspace access is resolved from persistent membership state.
    Role permissions continue to come exclusively from the
    server-side global role policy.
    """

    user_id: str
    workspace_id: str
    role: str
    permissions: frozenset[str]
    token_id: str | None = None

    def has_permission(
        self,
        permission: str,
    ) -> bool:
        return permission in self.permissions

def _authentication_error(
    detail: str,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_bearer_account_authorization_service(
) -> AccountAuthorizationService:
    """
    Provide authoritative account and role resolution for
    Bearer-token authentication.
    """
    return AccountAuthorizationService()

def get_current_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    authorization_service: Annotated[
        AccountAuthorizationService,
        Depends(
            get_bearer_account_authorization_service
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
    Resolve a workspace-bound principal from a signed Bearer token.

    The token must contain a workspace identifier. Account role,
    active workspace membership and workspace lifecycle state are
    revalidated from persistent server-side state on every request.
    """
    if credentials is None:
        authentication_logger.warning(
            "authentication_denied "
            "reason=missing_credentials"
        )

        raise _authentication_error(
            "Authentication required."
        )

    if credentials.scheme.lower() != "bearer":
        authentication_logger.warning(
            "authentication_denied "
            "reason=invalid_scheme"
        )

        raise _authentication_error(
            "Bearer authentication required."
        )

    payload = decode_access_token(
        credentials.credentials
    )

    if payload is None:
        authentication_logger.warning(
            "authentication_denied "
            "reason=invalid_or_expired_token"
        )

        raise _authentication_error(
            "Invalid or expired access token."
        )

    user_id = payload.get(
        "user_id"
    )

    role = normalize_role(
        payload.get(
            "role"
        )
    )

    workspace_id = payload.get(
        "workspace_id"
    )

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
    ):
        authentication_logger.warning(
            "authentication_denied "
            "reason=invalid_user_id"
        )

        raise _authentication_error(
            "Invalid authenticated principal."
        )

    if (
        not isinstance(workspace_id, str)
        or not workspace_id.strip()
    ):
        authentication_logger.warning(
            "authentication_denied "
            "user_id=%s "
            "reason=invalid_workspace_claim",
            user_id.strip(),
        )

        raise _authentication_error(
            "Invalid authenticated principal."
        )

    if not is_known_role(role):
        authentication_logger.warning(
            "authentication_denied "
            "user_id=%s reason=invalid_role role=%s",
            user_id.strip(),
            role or "not-recorded",
        )

        raise _authentication_error(
            "Invalid authenticated role."
        )

    try:
        authorization = (
            authorization_service.resolve(
                user_id.strip()
            )
        )

    except AccountAuthorizationError:
        authentication_logger.warning(
            "authentication_denied "
            "user_id=%s "
            "reason=account_revalidation_failed",
            user_id.strip(),
        )

        raise _authentication_error(
            "Invalid authenticated principal."
        )

    if (
        authorization.token_subject
        != user_id.strip()
        or authorization.canonical_role
        != role
    ):
        authentication_logger.warning(
            "authentication_denied "
            "user_id=%s "
            "reason=account_or_role_changed",
            user_id.strip(),
        )

        raise _authentication_error(
            "Invalid authenticated principal."
        )

    try:
        workspace_context = (
            workspace_context_resolver
            .resolve_requested(
                user_id=authorization.user_id,
                workspace_id=workspace_id.strip(),
            )
        )

    except WorkspaceRepositoryError:
        authentication_logger.warning(
            "authentication_denied "
            "user_id=%s workspace_id=%s "
            "reason=workspace_not_authorized",
            user_id.strip(),
            workspace_id.strip(),
        )

        raise _authentication_error(
            "Invalid authenticated principal."
        )

    principal = AuthenticatedPrincipal(
        user_id=authorization.token_subject,
        workspace_id=(
            workspace_context.workspace_id
        ),
        role=authorization.canonical_role,
        permissions=authorization.permissions,
        token_id=(
            str(
                payload["jti"]
            ).strip()
            if payload.get(
                "jti"
            )
            else None
        ),
    )

    authentication_logger.info(
        "authentication_granted "
        "user_id=%s workspace_id=%s "
        "role=%s token_id=%s",
        principal.user_id,
        principal.workspace_id,
        principal.role,
        principal.token_id
        or "not-recorded",
    )

    return principal

def get_current_user(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(get_current_principal),
    ],
) -> str:
    """
    Backward-compatible authenticated-user dependency.

    Existing routes that require only a user identifier may keep
    using get_current_user. New authorization-sensitive routes
    should depend on get_current_principal.
    """
    return principal.user_id
