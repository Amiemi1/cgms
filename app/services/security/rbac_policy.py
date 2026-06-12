ROLE_PERMISSIONS = {
    "admin": [
        "view_dashboard",
        "view_audit",
        "view_sessions",
        "manage_memory",
        "manage_users"
    ],
    "operator": [
        "view_dashboard",
        "view_audit",
        "view_sessions",
        "manage_memory"
    ],
    "viewer": [
        "view_dashboard",
        "view_audit"
    ]
}


def has_permission(role: str, permission: str) -> bool:
    role = role or "viewer"

    return permission in ROLE_PERMISSIONS.get(
        role,
        ROLE_PERMISSIONS["viewer"]
    )