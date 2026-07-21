from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import (
    SQLModel,
    Session,
    create_engine,
)

from app.db.models.security_models import (
    UserRole,
)
from app.db.models.user import User
from app.services.auth.credential_service import (
    AccountRoleConfigurationError,
    CredentialAuthenticationService,
    InvalidCredentialsError,
    normalize_email,
)
from app.services.auth.security import (
    hash_password,
)


TEST_PASSWORD = (
    "Correct-Horse-Battery-Staple-2026!"
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
) -> CredentialAuthenticationService:
    return CredentialAuthenticationService(
        session_factory=lambda: Session(
            engine
        )
    )


def add_user(
    engine,
    *,
    user_id: int,
    email: str,
    password: str = TEST_PASSWORD,
) -> None:
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                email=email,
                password_hash=hash_password(
                    password
                ),
            )
        )

        session.commit()


def add_role(
    engine,
    *,
    user_id: int,
    role: str,
    role_id: int,
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


def test_normalizes_email() -> None:
    assert normalize_email(
        "  ADMIN@Example.COM  "
    ) == "admin@example.com"


@pytest.mark.parametrize(
    "email",
    [
        "",
        " ",
        "not-an-email",
    ],
)
def test_invalid_email_is_rejected(
    email: str,
) -> None:
    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        normalize_email(email)


def test_authenticates_admin(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1001,
        email="Admin@Example.com",
    )

    add_role(
        engine,
        user_id=1001,
        role="admin",
        role_id=1,
    )

    account = create_service(
        engine
    ).authenticate(
        email=" admin@example.COM ",
        password=TEST_PASSWORD,
    )

    assert account.user_id == 1001
    assert account.email == (
        "admin@example.com"
    )
    assert account.canonical_role == "admin"
    assert account.stored_role == "admin"

    assert (
        account.used_legacy_alias
        is False
    )

    assert account.token_subject == "1001"


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
        user_id=1002,
        role="contributor",
        role_id=2,
    )

    account = create_service(
        engine
    ).authenticate(
        email="operator@example.com",
        password=TEST_PASSWORD,
    )

    assert (
        account.canonical_role
        == "operator"
    )

    assert (
        account.used_legacy_alias
        is True
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
        user_id=1003,
        role="reader",
        role_id=3,
    )

    account = create_service(
        engine
    ).authenticate(
        email="viewer@example.com",
        password=TEST_PASSWORD,
    )

    assert account.canonical_role == "viewer"
    assert account.used_legacy_alias is True


def test_missing_role_fails_closed(
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
        ).authenticate(
            email="unassigned@example.com",
            password=TEST_PASSWORD,
        )


def test_unknown_account_uses_generic_error(
    engine,
) -> None:
    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        create_service(
            engine
        ).authenticate(
            email="unknown@example.com",
            password=TEST_PASSWORD,
        )


def test_wrong_password_uses_same_generic_error(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1005,
        email="known@example.com",
    )

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        create_service(
            engine
        ).authenticate(
            email="known@example.com",
            password="Wrong-password-value",
        )


def test_blank_password_is_rejected(
    engine,
) -> None:
    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        create_service(
            engine
        ).authenticate(
            email="known@example.com",
            password="",
        )


def test_malformed_password_hash_is_denied(
    engine,
) -> None:
    with Session(engine) as session:
        session.add(
            User(
                id=1006,
                email="broken@example.com",
                password_hash=(
                    "not-a-valid-bcrypt-hash"
                ),
            )
        )

        session.commit()

    with pytest.raises(
        InvalidCredentialsError,
        match="Invalid email or password",
    ):
        create_service(
            engine
        ).authenticate(
            email="broken@example.com",
            password=TEST_PASSWORD,
        )


def test_unknown_stored_role_fails_closed(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1007,
        email="unknown-role@example.com",
    )

    add_role(
        engine,
        user_id=1007,
        role="superuser",
        role_id=7,
    )

    with pytest.raises(
        AccountRoleConfigurationError,
        match="role configuration",
    ):
        create_service(
            engine
        ).authenticate(
            email="unknown-role@example.com",
            password=TEST_PASSWORD,
        )


def test_conflicting_roles_fail_closed(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1008,
        email="conflict@example.com",
    )

    add_role(
        engine,
        user_id=1008,
        role="admin",
        role_id=8,
    )

    add_role(
        engine,
        user_id=1008,
        role="reader",
        role_id=9,
    )

    with pytest.raises(
        AccountRoleConfigurationError,
        match="conflicting role",
    ):
        create_service(
            engine
        ).authenticate(
            email="conflict@example.com",
            password=TEST_PASSWORD,
        )


def test_equivalent_roles_prefer_canonical_record(
    engine,
) -> None:
    add_user(
        engine,
        user_id=1009,
        email="equivalent@example.com",
    )

    add_role(
        engine,
        user_id=1009,
        role="contributor",
        role_id=10,
    )

    add_role(
        engine,
        user_id=1009,
        role="operator",
        role_id=11,
    )

    account = create_service(
        engine
    ).authenticate(
        email="equivalent@example.com",
        password=TEST_PASSWORD,
    )

    assert (
        account.canonical_role
        == "operator"
    )

    assert account.stored_role == "operator"

    assert (
        account.used_legacy_alias
        is False
    )