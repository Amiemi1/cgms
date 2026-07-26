from __future__ import annotations

from collections.abc import Collection


VIEW_DASHBOARD = (
    "view_dashboard"
)


VIEW_PATENT_GOVERNANCE = (
    "view_patent_governance"
)

VIEW_PATENT_SENSITIVE = (
    "view_patent_sensitive"
)

MANAGE_BROWSER_SESSIONS = (
    "manage_browser_sessions"
)


ROLE_PERMISSIONS: dict[
    str,
    frozenset[str],
] = {
    "admin": frozenset(
        {
            VIEW_DASHBOARD,
            "view_audit",
            "view_sessions",
            "manage_memory",
            "manage_users",
            MANAGE_BROWSER_SESSIONS,
            VIEW_PATENT_GOVERNANCE,
            VIEW_PATENT_SENSITIVE,
        }
    ),
    "operator": frozenset(
        {
            VIEW_DASHBOARD,
            "view_audit",
            "view_sessions",
            "manage_memory",
            VIEW_PATENT_GOVERNANCE,
        }
    ),
    "viewer": frozenset(
        {
            VIEW_DASHBOARD,
            "view_audit",
        }
    ),
}


def normalize_role(
    role: str | None,
) -> str:
    if not isinstance(role, str):
        return ""

    return role.strip().lower()


def is_known_role(
    role: str | None,
) -> bool:
    return (
        normalize_role(role)
        in ROLE_PERMISSIONS
    )


def get_permissions(
    role: str | None,
) -> frozenset[str]:
    """
    Return the permissions assigned to a recognized role.

    Unknown, blank or missing roles fail closed and receive no
    permissions. They are never silently treated as viewers.
    """
    normalized_role = normalize_role(
        role
    )

    return ROLE_PERMISSIONS.get(
        normalized_role,
        frozenset(),
    )


def has_permission(
    role: str | None,
    permission: str,
) -> bool:
    if not isinstance(permission, str):
        return False

    normalized_permission = (
        permission.strip()
    )

    if not normalized_permission:
        return False

    return (
        normalized_permission
        in get_permissions(role)
    )


def has_all_permissions(
    role: str | None,
    permissions: Collection[str],
) -> bool:
    assigned_permissions = (
        get_permissions(role)
    )

    normalized_permissions = {
        permission.strip()
        for permission in permissions
        if isinstance(permission, str)
        and permission.strip()
    }

    return normalized_permissions.issubset(
        assigned_permissions
    )