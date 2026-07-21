from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
    get_current_principal,
)


security_logger = logging.getLogger(
    "cgms.security.authorization"
)


def require_permission(
    permission: str,
) -> Callable[..., AuthenticatedPrincipal]:
    """
    Require a server-derived permission from an authenticated
    CGMS principal.

    Client-supplied role headers are never used for authorization.
    """
    normalized_permission = (
        permission.strip()
        if isinstance(permission, str)
        else ""
    )

    if not normalized_permission:
        raise ValueError(
            "A non-empty permission is required."
        )

    def checker(
        principal: Annotated[
            AuthenticatedPrincipal,
            Depends(get_current_principal),
        ],
    ) -> AuthenticatedPrincipal:
        if not principal.has_permission(
            normalized_permission
        ):
            security_logger.warning(
                "authorization_denied "
                "user_id=%s role=%s permission=%s token_id=%s",
                principal.user_id,
                principal.role,
                normalized_permission,
                principal.token_id or "not-recorded",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Permission denied: "
                    f"{normalized_permission}"
                ),
            )

        security_logger.info(
            "authorization_granted "
            "user_id=%s role=%s permission=%s token_id=%s",
            principal.user_id,
            principal.role,
            normalized_permission,
            principal.token_id or "not-recorded",
        )

        return principal

    return checker