from fastapi import Header, HTTPException
from app.services.security.rbac_policy import (
    has_permission
)


def require_permission(permission: str):

    def checker(
        x_user_role: str = Header(default="viewer")
    ):

        if not has_permission(
            x_user_role,
            permission
        ):

            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission}"
            )

        return {
            "role": x_user_role,
            "permission": permission
        }

    return checker