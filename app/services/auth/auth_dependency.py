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


security = HTTPBearer(
    auto_error=False
)

authentication_logger = logging.getLogger(
    "cgms.security.authentication"
)


@dataclass(
    frozen=True,
    slots=True,
)
class AuthenticatedPrincipal:
    """
    Server-validated identity used for CGMS authorization.

    Permissions are derived from the server-side role policy.
    They are never accepted directly from request headers or
    untrusted token permission claims.
    """

    user_id: str
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


def get_current_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
) -> AuthenticatedPrincipal:
    """
    Resolve a verified CGMS principal from a signed Bearer token.

    Missing, invalid, expired or structurally incomplete tokens
    fail closed with HTTP 401.
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

    user_id = payload.get("user_id")
    role = normalize_role(
        payload.get("role")
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

    principal = AuthenticatedPrincipal(
        user_id=user_id.strip(),
        role=role,
        permissions=get_permissions(role),
        token_id=(
            str(payload["jti"]).strip()
            if payload.get("jti")
            else None
        ),
    )

    authentication_logger.info(
        "authentication_granted "
        "user_id=%s role=%s token_id=%s",
        principal.user_id,
        principal.role,
        principal.token_id or "not-recorded",
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