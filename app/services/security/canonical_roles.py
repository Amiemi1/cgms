from __future__ import annotations

from dataclasses import dataclass

from app.services.security.rbac_policy import (
    ROLE_PERMISSIONS,
    normalize_role,
)


CANONICAL_ADMIN = "admin"
CANONICAL_OPERATOR = "operator"
CANONICAL_VIEWER = "viewer"

CANONICAL_ROLES = frozenset(
    {
        CANONICAL_ADMIN,
        CANONICAL_OPERATOR,
        CANONICAL_VIEWER,
    }
)

LEGACY_ROLE_ALIASES: dict[str, str] = {
    "admin": CANONICAL_ADMIN,
    "operator": CANONICAL_OPERATOR,
    "viewer": CANONICAL_VIEWER,
    "contributor": CANONICAL_OPERATOR,
    "reader": CANONICAL_VIEWER,
}


class CanonicalRoleResolutionError(ValueError):
    """
    Raised when a stored or supplied role cannot be mapped to a
    recognized authenticated CGMS role.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class CanonicalRoleResolution:
    supplied_role: str
    normalized_role: str
    canonical_role: str
    used_legacy_alias: bool

    @property
    def permissions(
        self,
    ) -> frozenset[str]:
        return ROLE_PERMISSIONS[
            self.canonical_role
        ]


def is_canonical_role(
    role: str | None,
) -> bool:
    return normalize_role(role) in CANONICAL_ROLES


def resolve_canonical_role(
    role: str | None,
    *,
    fail_closed: bool = True,
    default_role: str | None = None,
) -> CanonicalRoleResolution:
    """
    Convert canonical and legacy role values into the current
    authenticated RBAC vocabulary.

    Supported mappings:

    admin       -> admin
    operator    -> operator
    viewer      -> viewer
    contributor -> operator
    reader      -> viewer

    Unknown roles fail closed unless an explicit recognized
    default_role is supplied.
    """
    supplied_role = (
        role
        if isinstance(role, str)
        else ""
    )

    normalized_role = normalize_role(
        supplied_role
    )

    canonical_role = LEGACY_ROLE_ALIASES.get(
        normalized_role
    )

    if canonical_role is None:
        normalized_default = normalize_role(
            default_role
        )

        if normalized_default:
            canonical_role = (
                LEGACY_ROLE_ALIASES.get(
                    normalized_default
                )
            )

            if canonical_role is None:
                raise CanonicalRoleResolutionError(
                    "The configured default role is not "
                    "recognized."
                )

        elif fail_closed:
            raise CanonicalRoleResolutionError(
                "The supplied role is not recognized."
            )

        else:
            canonical_role = CANONICAL_VIEWER

    if canonical_role not in ROLE_PERMISSIONS:
        raise CanonicalRoleResolutionError(
            "The resolved canonical role is not present "
            "in the RBAC permission catalogue."
        )

    return CanonicalRoleResolution(
        supplied_role=supplied_role,
        normalized_role=normalized_role,
        canonical_role=canonical_role,
        used_legacy_alias=(
            bool(normalized_role)
            and normalized_role
            != canonical_role
        ),
    )


def canonical_role_name(
    role: str | None,
) -> str:
    return resolve_canonical_role(
        role
    ).canonical_role