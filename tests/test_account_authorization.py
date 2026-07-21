from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import (
    SQLModel,
    Session,
    create_engine,
)

from app.db.models.security_models import UserRole
from app.db.models.user import User
from app.services.auth.account_authorization import (
    AccountAuthorizationService,
    AccountNotFoundError,
    AccountRoleConfigurationError,
    InvalidAccountIdentifierError,
    normalize_account_identifier,
    resolve_account_role_records,
)


@pytest.fixture()
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(
        test_engine
    )

    return test_engine


def create_service(
    engine,
) -> AccountAuthorizationService:
    return AccountAuthorizationService(
        session_factory=lambda: Session(
            engine
        )
    )


def add_user(
    engine,
    *,
    user_id: int,
    email: str,
) -> None:
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                email=email,
                password_hash=(
                    "password-hash-not-used-"
                    "by-authorization-tests"
                ),
            )
        )

        session.commit()


def add_role(
    engine,
    *,
    role_id: int,
    user_id: int,
    role: str,
) -> None:
    with Session(engine) as session:
        session.add(
            UserRole(
                id=role_id,
                user_id=user_id,
                role=role,
            )
        )

        session.commit()


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        (1, 1),
        (1001, 1001),
        ("1", 1),
        ("1001", 1001),
        (" 1001 ", 1001),
    ],
)
def test_normalizes_account_identifier(
    supplied: str | int,
    expected: int,
) -> None:
    assert (
        normalize_account_identifier(
            supplied
        )
        == expected
    )


@pytest.mark.parametrize(
    "supplied",
    [
        True,
        False,
        0,
        -1,
        "",
        " ",
        "abc",
        "1.5",
        "-1",
        "+1",
        None,
    ],
)
def test_invalid_account_identifiers_fail_closed(
    supplied,
) -> None:
    with pytest.raises(
        InvalidAccountIdentifierError,
        match="Invalid authenticated account",
    ):
        normalize_account_identifier(
            supplied
        )


def test_resolves_admin_account(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1001,
        email="admin@example.com",
    )

    add_role(
        engine,
        role_id=1,
        user_id=1001,
        role="admin",
    )

    authorization = create_service(
        engine
    ).resolve("1001")

    assert authorization.user_id == 1001
    assert authorization.email == (
        "admin@example.com"
    )
    assert authorization.stored_role == "admin"
    assert authorization.canonical_role == "admin"

    assert (
        authorization.used_legacy_alias
        is False
    )

    assert (
        "view_patent_sensitive"
        in authorization.permissions
    )

    assert authorization.token_subject == "1001"


def test_contributor_maps_to_operator(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1002,
        email="operator@example.com",
    )

    add_role(
        engine,
        role_id=2,
        user_id=1002,
        role="contributor",
    )

    authorization = create_service(
        engine
    ).resolve(1002)

    assert (
        authorization.stored_role
        == "contributor"
    )

    assert (
        authorization.canonical_role
        == "operator"
    )

    assert (
        authorization.used_legacy_alias
        is True
    )

    assert (
        "view_patent_governance"
        in authorization.permissions
    )

    assert (
        "view_patent_sensitive"
        not in authorization.permissions
    )


def test_reader_maps_to_viewer(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1003,
        email="viewer@example.com",
    )

    add_role(
        engine,
        role_id=3,
        user_id=1003,
        role="reader",
    )

    authorization = create_service(
        engine
    ).resolve(1003)

    assert (
        authorization.canonical_role
        == "viewer"
    )

    assert (
        authorization.used_legacy_alias
        is True
    )

    assert (
        "view_patent_governance"
        not in authorization.permissions
    )


def test_missing_account_fails_closed(
    engine,
) -> None:
    with pytest.raises(
        AccountNotFoundError,
        match="account is unavailable",
    ):
        create_service(
            engine
        ).resolve(9999)


def test_account_without_role_fails_closed(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1004,
        email="unassigned@example.com",
    )

    with pytest.raises(
        AccountRoleConfigurationError,
        match="role assignment is missing",
    ):
        create_service(
            engine
        ).resolve(1004)


def test_unknown_role_fails_closed(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1005,
        email="unknown@example.com",
    )

    add_role(
        engine,
        role_id=5,
        user_id=1005,
        role="superuser",
    )

    with pytest.raises(
        AccountRoleConfigurationError,
        match="role configuration is invalid",
    ):
        create_service(
            engine
        ).resolve(1005)


def test_conflicting_roles_fail_closed(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1006,
        email="conflict@example.com",
    )

    add_role(
        engine,
        role_id=6,
        user_id=1006,
        role="admin",
    )

    add_role(
        engine,
        role_id=7,
        user_id=1006,
        role="viewer",
    )

    with pytest.raises(
        AccountRoleConfigurationError,
        match="conflicting role assignments",
    ):
        create_service(
            engine
        ).resolve(1006)


def test_equivalent_roles_prefer_canonical_record(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1007,
        email="equivalent@example.com",
    )

    add_role(
        engine,
        role_id=8,
        user_id=1007,
        role="contributor",
    )

    add_role(
        engine,
        role_id=9,
        user_id=1007,
        role="operator",
    )

    authorization = create_service(
        engine
    ).resolve(1007)

    assert (
        authorization.canonical_role
        == "operator"
    )

    assert (
        authorization.stored_role
        == "operator"
    )

    assert (
        authorization.used_legacy_alias
        is False
    )


def test_duplicate_same_role_is_permitted(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1008,
        email="duplicate@example.com",
    )

    add_role(
        engine,
        role_id=10,
        user_id=1008,
        role="viewer",
    )

    add_role(
        engine,
        role_id=11,
        user_id=1008,
        role="viewer",
    )

    authorization = create_service(
        engine
    ).resolve(1008)

    assert (
        authorization.canonical_role
        == "viewer"
    )


def test_role_record_resolver_requires_assignment() -> None:
    with pytest.raises(
        AccountRoleConfigurationError,
        match="role assignment is missing",
    ):
        resolve_account_role_records(
            [],
            user_id=2001,
        )


def test_role_record_resolver_rejects_unknown_role() -> None:
    with pytest.raises(
        AccountRoleConfigurationError,
        match="role configuration is invalid",
    ):
        resolve_account_role_records(
            [
                UserRole(
                    id=1,
                    user_id=2002,
                    role="owner",
                )
            ],
            user_id=2002,
        )


def test_role_record_resolver_rejects_conflicts() -> None:
    with pytest.raises(
        AccountRoleConfigurationError,
        match="conflicting role assignments",
    ):
        resolve_account_role_records(
            [
                UserRole(
                    id=1,
                    user_id=2003,
                    role="admin",
                ),
                UserRole(
                    id=2,
                    user_id=2003,
                    role="reader",
                ),
            ],
            user_id=2003,
        )