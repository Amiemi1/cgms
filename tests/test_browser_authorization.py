from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.services.auth.account_authorization import (
    AccountNotFoundError,
    AccountRoleConfigurationError,
    InvalidAccountIdentifierError,
    ResolvedAccountAuthorization,
)
from app.services.auth.browser_authorization import (
    BrowserSessionAuthorizationError,
    revalidate_browser_session,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
)
from app.services.security.rbac_policy import (
    VIEW_PATENT_GOVERNANCE,
    VIEW_PATENT_SENSITIVE,
    get_permissions,
)


class StubAuthorizationService:
    def __init__(
        self,
        *,
        authorization= None,
        error: Exception | None = None,
    ) -> None:
        self.authorization = authorization
        self.error = error
        self.calls: list[str | int] = []

    def resolve(
        self,
        user_id: str | int,
    ) -> ResolvedAccountAuthorization:
        self.calls.append(user_id)

        if self.error is not None:
            raise self.error

        if self.authorization is None:
            raise AssertionError(
                "No authorization result configured."
            )

        return self.authorization


def build_identity(
    *,
    user_id: str = "1001",
    role: str = "operator",
) -> BrowserSessionIdentity:
    issued_at = datetime.now(
        timezone.utc
    )

    return BrowserSessionIdentity(
        user_id=user_id,
        role=role,
        token_id="session-token-id-1001",
        issued_at=issued_at,
        expires_at=(
            issued_at
            + timedelta(minutes=30)
        ),
    )


def build_authorization(
    *,
    user_id: int = 1001,
    stored_role: str = "operator",
    canonical_role: str = "operator",
    used_legacy_alias: bool = False,
) -> ResolvedAccountAuthorization:
    return ResolvedAccountAuthorization(
        user_id=user_id,
        email="user@example.com",
        stored_role=stored_role,
        canonical_role=canonical_role,
        used_legacy_alias=used_legacy_alias,
        permissions=get_permissions(
            canonical_role
        ),
    )


def test_matching_current_role_creates_principal() -> None:
    service = StubAuthorizationService(
        authorization=build_authorization()
    )

    principal = revalidate_browser_session(
        identity=build_identity(),
        service=service,
    )

    assert principal.user_id == "1001"
    assert principal.role == "operator"

    assert (
        VIEW_PATENT_GOVERNANCE
        in principal.permissions
    )

    assert (
        VIEW_PATENT_SENSITIVE
        not in principal.permissions
    )

    assert (
        principal.token_id
        == "session-token-id-1001"
    )

    assert service.calls == ["1001"]


def test_admin_permissions_come_from_current_policy() -> None:
    service = StubAuthorizationService(
        authorization=build_authorization(
            stored_role="admin",
            canonical_role="admin",
        )
    )

    principal = revalidate_browser_session(
        identity=build_identity(
            role="admin"
        ),
        service=service,
    )

    assert principal.role == "admin"

    assert (
        VIEW_PATENT_SENSITIVE
        in principal.permissions
    )


def test_legacy_role_record_can_resolve_canonically() -> None:
    service = StubAuthorizationService(
        authorization=build_authorization(
            stored_role="contributor",
            canonical_role="operator",
            used_legacy_alias=True,
        )
    )

    principal = revalidate_browser_session(
        identity=build_identity(
            role="operator"
        ),
        service=service,
    )

    assert principal.role == "operator"

    assert (
        VIEW_PATENT_GOVERNANCE
        in principal.permissions
    )


@pytest.mark.parametrize(
    ("session_role", "current_role"),
    [
        ("admin", "operator"),
        ("operator", "viewer"),
        ("viewer", "operator"),
        ("operator", "admin"),
    ],
)
def test_changed_role_invalidates_session(
    session_role: str,
    current_role: str,
) -> None:
    service = StubAuthorizationService(
        authorization=build_authorization(
            stored_role=current_role,
            canonical_role=current_role,
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(
                role=session_role
            ),
            service=service,
        )

    assert error.value.reason == "role_changed"


def test_deleted_account_invalidates_session() -> None:
    service = StubAuthorizationService(
        error=AccountNotFoundError(
            "Authenticated account is unavailable."
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(),
            service=service,
        )

    assert (
        error.value.reason
        == "account_not_found"
    )


def test_invalid_role_configuration_invalidates_session() -> None:
    service = StubAuthorizationService(
        error=AccountRoleConfigurationError(
            "Account role configuration is invalid."
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(),
            service=service,
        )

    assert (
        error.value.reason
        == "invalid_role_configuration"
    )


def test_invalid_account_identifier_invalidates_session() -> None:
    service = StubAuthorizationService(
        error=InvalidAccountIdentifierError(
            "Invalid authenticated account."
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(
                user_id="invalid"
            ),
            service=service,
        )

    assert (
        error.value.reason
        == "invalid_account_identifier"
    )


def test_noncanonical_numeric_identifier_is_rejected() -> None:
    service = StubAuthorizationService(
        authorization=build_authorization(
            user_id=1001
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(
                user_id="01001"
            ),
            service=service,
        )

    assert (
        error.value.reason
        == "noncanonical_account_identifier"
    )


def test_unknown_session_role_is_rejected() -> None:
    service = StubAuthorizationService(
        authorization=build_authorization()
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(
                role="superuser"
            ),
            service=service,
        )

    assert (
        error.value.reason
        == "invalid_session_role"
    )

    assert service.calls == []


def test_failure_message_does_not_disclose_reason() -> None:
    service = StubAuthorizationService(
        error=AccountNotFoundError(
            "Authenticated account is unavailable."
        )
    )

    with pytest.raises(
        BrowserSessionAuthorizationError
    ) as error:
        revalidate_browser_session(
            identity=build_identity(),
            service=service,
        )

    assert str(error.value) == (
        "Browser session is no longer authorized."
    )

    assert (
        "account_not_found"
        not in str(error.value)
    )