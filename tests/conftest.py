import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT_DIR)
)

# AAE-001 LEGACY APPLICATION AUTHENTICATION HARNESS
#
# These named modules predate application-wide authorization.
# Their business assertions now execute through the real global
# guard using signed credentials. The guard itself is never
# bypassed.
from pathlib import Path as _AAEPath

import pytest as _aae_pytest


_AAE_LEGACY_BEARER_TEST_FILES = frozenset(
    {
        "test_admin_summary.py",
        "test_commercial_layer.py",
        "test_connector_adapters.py",
        "test_connectors.py",
        "test_enterprise_readiness.py",
        "test_environment_manifest.py",
        "test_external_ingestion.py",
        "test_memory_intelligence.py",
        "test_ops_observability.py",
        "test_persistence_layer.py",
        "test_product_readiness_api.py",
        "test_release_readiness.py",
        "test_runtime_metrics.py",
        "test_system_health.py",
        "test_workspace_quota.py",
        "test_workspace_runtime.py",
    }
)

_AAE_LEGACY_BROWSER_TEST_FILE = (
    "test_product_readiness_dashboard.py"
)

_AAE_LEGACY_CLIENT_FACTORY_TEST_FILE = (
    "test_product_readiness_bootstrap.py"
)

_AAE_ADMIN_USER_ID = "9001"
_AAE_ADMIN_ROLE = "admin"


def _aae_create_admin_bearer_token() -> str:
    from app.services.auth.jwt_handler import (
        create_access_token,
    )

    return create_access_token(
        {
            "user_id": _AAE_ADMIN_USER_ID,
            "role": _AAE_ADMIN_ROLE,
        }
    )


def _aae_create_admin_browser_token() -> str:
    from app.services.auth.browser_session import (
        SESSION_TOKEN_USE,
    )
    from app.services.auth.jwt_handler import (
        create_access_token,
    )

    return create_access_token(
        {
            "user_id": _AAE_ADMIN_USER_ID,
            "role": _AAE_ADMIN_ROLE,
            "token_use": SESSION_TOKEN_USE,
        }
    )


class _AAELegacyActiveSessionRegistry:
    def require_active(
        self,
        identity,
    ) -> object:
        return object()


class _AAELegacyAdminAuthorizationService:
    def resolve(
        self,
        user_id,
    ):
        from app.services.auth.account_authorization import (
            ResolvedAccountAuthorization,
        )
        from app.services.security.rbac_policy import (
            get_permissions,
        )

        normalized_user_id = int(
            str(user_id).strip()
        )

        return ResolvedAccountAuthorization(
            user_id=normalized_user_id,
            email=(
                "aae-legacy-admin"
                "@example.com"
            ),
            stored_role=_AAE_ADMIN_ROLE,
            canonical_role=_AAE_ADMIN_ROLE,
            used_legacy_alias=False,
            permissions=get_permissions(
                _AAE_ADMIN_ROLE
            ),
        )


def _aae_restore_header(
    headers,
    name: str,
    previous_value: str | None,
) -> None:
    if previous_value is not None:
        headers[name] = previous_value
        return

    try:
        del headers[name]
    except KeyError:
        pass


def _aae_restore_dependency_override(
    application,
    dependency,
    previous_value,
    missing_sentinel,
) -> None:
    if previous_value is missing_sentinel:
        application.dependency_overrides.pop(
            dependency,
            None,
        )
        return

    application.dependency_overrides[
        dependency
    ] = previous_value


@_aae_pytest.fixture(
    autouse=True,
)
def _aae_authenticate_legacy_application_test(
    request,
    monkeypatch,
):
    """
    Supply real signed test credentials only to the named legacy
    endpoint modules whose original business assertions assumed
    anonymous access before AAE-001.

    Dedicated anonymous-denial and authorization-policy tests
    remain unchanged.
    """
    test_file_name = _AAEPath(
        str(request.fspath)
    ).name

    if (
        test_file_name
        in _AAE_LEGACY_BEARER_TEST_FILES
    ):
        client = getattr(
            request.module,
            "client",
            None,
        )

        if client is None:
            raise RuntimeError(
                "Expected a module-level TestClient in "
                f"{test_file_name}."
            )

        previous_authorization = (
            client.headers.get(
                "Authorization"
            )
        )

        client.headers[
            "Authorization"
        ] = (
            "Bearer "
            + _aae_create_admin_bearer_token()
        )

        try:
            yield

        finally:
            _aae_restore_header(
                client.headers,
                "Authorization",
                previous_authorization,
            )

        return

    if (
        test_file_name
        == _AAE_LEGACY_BROWSER_TEST_FILE
    ):
        from app.dashboard.main import app
        from app.services.auth.browser_session import (
            get_browser_session_settings,
        )
        from app.services.auth.browser_session_dependency import (
            get_account_authorization_service,
            get_browser_session_registry,
        )

        client = getattr(
            request.module,
            "client",
            None,
        )

        if client is None:
            raise RuntimeError(
                "Expected a module-level TestClient in "
                f"{test_file_name}."
            )

        cookie_name = (
            get_browser_session_settings()
            .cookie_name
        )

        previous_cookie = client.headers.get(
            "Cookie"
        )

        missing = object()

        previous_registry_override = (
            app.dependency_overrides.get(
                get_browser_session_registry,
                missing,
            )
        )

        previous_authorization_override = (
            app.dependency_overrides.get(
                get_account_authorization_service,
                missing,
            )
        )

        app.dependency_overrides[
            get_browser_session_registry
        ] = (
            lambda:
            _AAELegacyActiveSessionRegistry()
        )

        app.dependency_overrides[
            get_account_authorization_service
        ] = (
            lambda:
            _AAELegacyAdminAuthorizationService()
        )

        client.headers["Cookie"] = (
            f"{cookie_name}="
            f"{_aae_create_admin_browser_token()}"
        )

        try:
            yield

        finally:
            _aae_restore_header(
                client.headers,
                "Cookie",
                previous_cookie,
            )

            _aae_restore_dependency_override(
                app,
                get_browser_session_registry,
                previous_registry_override,
                missing,
            )

            _aae_restore_dependency_override(
                app,
                get_account_authorization_service,
                previous_authorization_override,
                missing,
            )

        return

    if (
        test_file_name
        == _AAE_LEGACY_CLIENT_FACTORY_TEST_FILE
    ):
        original_test_client = getattr(
            request.module,
            "TestClient",
            None,
        )

        if original_test_client is None:
            raise RuntimeError(
                "Expected TestClient constructor in "
                f"{test_file_name}."
            )

        bearer_token = (
            _aae_create_admin_bearer_token()
        )

        def authenticated_test_client(
            *args,
            **kwargs,
        ):
            supplied_headers = kwargs.pop(
                "headers",
                None,
            )

            headers = dict(
                supplied_headers or {}
            )

            headers.setdefault(
                "Authorization",
                f"Bearer {bearer_token}",
            )

            return original_test_client(
                *args,
                headers=headers,
                **kwargs,
            )

        monkeypatch.setattr(
            request.module,
            "TestClient",
            authenticated_test_client,
        )

        yield
        return

    yield
