from __future__ import annotations

import pytest

from app.services.security.canonical_roles import (
    CANONICAL_ADMIN,
    CANONICAL_OPERATOR,
    CANONICAL_VIEWER,
    CanonicalRoleResolutionError,
    canonical_role_name,
    is_canonical_role,
    resolve_canonical_role,
)
from app.services.security.rbac_policy import (
    VIEW_PATENT_GOVERNANCE,
    VIEW_PATENT_SENSITIVE,
)


@pytest.mark.parametrize(
    ("supplied_role", "expected_role"),
    [
        ("admin", CANONICAL_ADMIN),
        ("operator", CANONICAL_OPERATOR),
        ("viewer", CANONICAL_VIEWER),
        ("contributor", CANONICAL_OPERATOR),
        ("reader", CANONICAL_VIEWER),
        (" ADMIN ", CANONICAL_ADMIN),
        ("Contributor", CANONICAL_OPERATOR),
        ("READER", CANONICAL_VIEWER),
    ],
)
def test_resolves_canonical_and_legacy_roles(
    supplied_role: str,
    expected_role: str,
) -> None:
    resolution = resolve_canonical_role(
        supplied_role
    )

    assert (
        resolution.canonical_role
        == expected_role
    )


def test_marks_legacy_aliases() -> None:
    contributor = resolve_canonical_role(
        "contributor"
    )

    reader = resolve_canonical_role(
        "reader"
    )

    operator = resolve_canonical_role(
        "operator"
    )

    assert contributor.used_legacy_alias is True
    assert reader.used_legacy_alias is True
    assert operator.used_legacy_alias is False


def test_resolved_permissions_come_from_rbac_policy() -> None:
    admin = resolve_canonical_role("admin")
    operator = resolve_canonical_role(
        "contributor"
    )
    viewer = resolve_canonical_role("reader")

    assert (
        VIEW_PATENT_GOVERNANCE
        in admin.permissions
    )

    assert (
        VIEW_PATENT_SENSITIVE
        in admin.permissions
    )

    assert (
        VIEW_PATENT_GOVERNANCE
        in operator.permissions
    )

    assert (
        VIEW_PATENT_SENSITIVE
        not in operator.permissions
    )

    assert (
        VIEW_PATENT_GOVERNANCE
        not in viewer.permissions
    )


@pytest.mark.parametrize(
    "role",
    [
        None,
        "",
        " ",
        "superuser",
        "patent_admin",
        "owner",
    ],
)
def test_unknown_roles_fail_closed(
    role: str | None,
) -> None:
    with pytest.raises(
        CanonicalRoleResolutionError
    ):
        resolve_canonical_role(role)


def test_explicit_recognized_default_can_be_used() -> None:
    resolution = resolve_canonical_role(
        None,
        default_role="reader",
    )

    assert (
        resolution.canonical_role
        == CANONICAL_VIEWER
    )


def test_invalid_default_role_fails() -> None:
    with pytest.raises(
        CanonicalRoleResolutionError
    ):
        resolve_canonical_role(
            None,
            default_role="unknown-role",
        )


def test_non_failing_mode_defaults_to_viewer() -> None:
    resolution = resolve_canonical_role(
        "unknown-role",
        fail_closed=False,
    )

    assert (
        resolution.canonical_role
        == CANONICAL_VIEWER
    )


def test_canonical_role_name_returns_string() -> None:
    assert (
        canonical_role_name("contributor")
        == CANONICAL_OPERATOR
    )


def test_is_canonical_role_excludes_legacy_aliases() -> None:
    assert is_canonical_role("admin") is True
    assert is_canonical_role("operator") is True
    assert is_canonical_role("viewer") is True

    assert (
        is_canonical_role("contributor")
        is False
    )

    assert is_canonical_role("reader") is False