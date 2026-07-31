from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.dashboard.routes.browser_session_administration import (
    get_session_administration_service,
    router,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_csrf import (
    issue_browser_csrf_token,
)
from app.services.auth.browser_session_dependency import (
    get_current_browser_principal,
)
from app.services.security.rbac_policy import (
    get_permissions,
)
from app.services.security.session_administration import (
    AdministrativeSessionRevocationResult,
    SessionAdministrationInputError,
    SessionAdministrationPermissionError,
    SessionAdministrationPersistenceError,
)


TEST_JWT_SECRET = (
    "cgms-session-administration-route-test-"
    "secret-with-more-than-32-characters"
)

CSRF_COOKIE_NAME = "__Host-cgms_csrf"

RESULT_TIME = datetime(
    2026,
    7,
    22,
    12,
    30,
    tzinfo=timezone.utc,
)


@pytest.fixture(autouse=True)
def configure_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CGMS_JWT_SECRET",
        TEST_JWT_SECRET,
    )

    monkeypatch.setenv(
        "CGMS_JWT_ISSUER",
        "cgms-session-administration-route-test",
    )

    monkeypatch.setenv(
        "CGMS_JWT_AUDIENCE",
        "cgms-session-administration-dashboard",
    )

    monkeypatch.setenv(
        "CGMS_CSRF_COOKIE_NAME",
        CSRF_COOKIE_NAME,
    )

    monkeypatch.setenv(
        "CGMS_CSRF_EXPIRE_SECONDS",
        "600",
    )


class StubSessionAdministrationService:
    def __init__(
        self,
        *,
        result: (
            AdministrativeSessionRevocationResult
            | None
        ) = None,
        error: Exception | None = None,
    ) -> None:
        self.result = (
            result
            or AdministrativeSessionRevocationResult(
                actor_user_id=9001,
                target_user_id=1001,
                revoked_count=2,
                reason="admin_revocation",
                revoked_at=RESULT_TIME,
            )
        )

        self.error = error

        self.calls: list[
            tuple[
                AuthenticatedPrincipal,
                str | int,
                str,
            ]
        ] = []

    def revoke_user_sessions(
        self,
        *,
        actor: AuthenticatedPrincipal,
        target_user_id: str | int,
        reason: str = "admin_revocation",
    ) -> AdministrativeSessionRevocationResult:
        self.calls.append(
            (
                actor,
                target_user_id,
                reason,
            )
        )

        if self.error is not None:
            raise self.error

        return self.result


def build_principal(
    role: str,
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        workspace_id="default",
        user_id=(
            "9001"
            if role == "admin"
            else "8001"
        ),
        role=role,
        permissions=get_permissions(
            role
        ),
        token_id=(
            f"{role}-browser-session"
        ),
    )


def build_app(
    *,
    role: str = "admin",
    service: (
        StubSessionAdministrationService
        | None
    ) = None,
    override_principal: bool = True,
) -> FastAPI:
    app = FastAPI()

    active_service = (
        service
        or StubSessionAdministrationService()
    )

    app.include_router(
        router
    )

    app.dependency_overrides[
        get_session_administration_service
    ] = lambda: active_service

    if override_principal:
        principal = build_principal(
            role
        )

        app.dependency_overrides[
            get_current_browser_principal
        ] = lambda: principal

    return app


def build_client(
    *,
    role: str = "admin",
    service: (
        StubSessionAdministrationService
        | None
    ) = None,
    override_principal: bool = True,
) -> TestClient:
    return TestClient(
        build_app(
            role=role,
            service=service,
            override_principal=(
                override_principal
            ),
        ),
        base_url="https://testserver",
    )


def csrf_headers(
    csrf_token: str,
) -> dict[str, str]:
    return {
        "Cookie": (
            f"{CSRF_COOKIE_NAME}="
            f"{csrf_token}"
        ),
    }


def submit_revocation(
    client: TestClient,
    *,
    csrf_token: str,
    target_user_id: str = "1001",
    reason: str | None = None,
):
    form_data = {
        "csrf_token": csrf_token,
        "target_user_id": target_user_id,
    }

    if reason is not None:
        form_data["reason"] = reason

    return client.post(
        "/admin/browser-sessions/revoke-user",
        data=form_data,
        headers=csrf_headers(
            csrf_token
        ),
    )


def test_admin_can_revoke_target_sessions(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "completed",
        "target_user_id": 1001,
        "revoked_count": 2,
        "reason": "admin_revocation",
        "revoked_at": (
            RESULT_TIME.isoformat()
        ),
    }

    assert len(service.calls) == 1

    actor, target_user_id, reason = (
        service.calls[0]
    )

    assert actor.role == "admin"
    assert target_user_id == "1001"
    assert reason == "admin_revocation"

    assert (
        response.headers["cache-control"]
        == "no-store, max-age=0"
    )


def test_custom_reason_is_forwarded(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
        reason="security_incident",
    )

    assert response.status_code == 200

    assert (
        service.calls[0][2]
        == "security_incident"
    )


def test_zero_revocations_are_successful(
) -> None:
    service = StubSessionAdministrationService(
        result=(
            AdministrativeSessionRevocationResult(
                actor_user_id=9001,
                target_user_id=1001,
                revoked_count=0,
                reason="admin_revocation",
                revoked_at=RESULT_TIME,
            )
        )
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 200
    assert response.json()["revoked_count"] == 0


@pytest.mark.parametrize(
    "role",
    [
        "operator",
        "viewer",
    ],
)
def test_non_admin_role_is_denied(
    role: str,
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        role=role,
        service=service,
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 403
    assert service.calls == []


def test_missing_browser_session_is_denied(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service,
        override_principal=False,
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 401
    assert service.calls == []


def test_missing_csrf_cookie_is_rejected(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = client.post(
        "/admin/browser-sessions/revoke-user",
        data={
            "csrf_token": csrf_token,
            "target_user_id": "1001",
        },
    )

    assert response.status_code == 400
    assert service.calls == []


def test_mismatched_csrf_token_is_rejected(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    submitted_token = (
        issue_browser_csrf_token()
    )

    cookie_token = (
        issue_browser_csrf_token()
    )

    response = client.post(
        "/admin/browser-sessions/revoke-user",
        data={
            "csrf_token": submitted_token,
            "target_user_id": "1001",
        },
        headers=csrf_headers(
            cookie_token
        ),
    )

    assert response.status_code == 400
    assert service.calls == []


def test_json_request_is_rejected(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = client.post(
        "/admin/browser-sessions/revoke-user",
        json={
            "csrf_token": csrf_token,
            "target_user_id": "1001",
        },
        headers=csrf_headers(
            csrf_token
        ),
    )

    assert response.status_code == 400
    assert service.calls == []


def test_missing_target_identifier_is_rejected(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = client.post(
        "/admin/browser-sessions/revoke-user",
        data={
            "csrf_token": csrf_token,
        },
        headers=csrf_headers(
            csrf_token
        ),
    )

    assert response.status_code == 400
    assert service.calls == []


def test_duplicate_target_identifier_is_rejected(
) -> None:
    service = (
        StubSessionAdministrationService()
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    body = (
        f"csrf_token={csrf_token}"
        "&target_user_id=1001"
        "&target_user_id=2001"
    )

    response = client.post(
        "/admin/browser-sessions/revoke-user",
        content=body,
        headers={
            **csrf_headers(
                csrf_token
            ),
            "Content-Type": (
                "application/x-www-form-urlencoded"
            ),
        },
    )

    assert response.status_code == 400
    assert service.calls == []


def test_service_input_error_returns_400(
) -> None:
    service = StubSessionAdministrationService(
        error=SessionAdministrationInputError(
            "Invalid target."
        )
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
        target_user_id="invalid",
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "The session revocation request "
            "could not be validated."
        )
    }


def test_service_permission_error_returns_403(
) -> None:
    service = StubSessionAdministrationService(
        error=(
            SessionAdministrationPermissionError(
                "Permission denied."
            )
        )
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 403


def test_persistence_error_returns_503(
) -> None:
    service = StubSessionAdministrationService(
        error=(
            SessionAdministrationPersistenceError(
                "Persistence failed."
            )
        )
    )

    client = build_client(
        service=service
    )

    csrf_token = issue_browser_csrf_token()

    response = submit_revocation(
        client,
        csrf_token=csrf_token,
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Session revocation could not "
            "be completed."
        )
    }

    assert (
        response.headers["cache-control"]
        == "no-store, max-age=0"
    )


def test_route_is_post_only(
) -> None:
    client = build_client()

    response = client.get(
        "/admin/browser-sessions/revoke-user"
    )

    assert response.status_code == 405
