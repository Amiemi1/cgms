from __future__ import annotations

import logging
from typing import Annotated, Final

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
)

from app.services.auth.account_authorization import (
    AccountAuthorizationService,
)
from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
    get_current_principal,
    security,
)
from app.services.auth.browser_csrf import (
    BrowserCsrfValidationError,
    validate_browser_csrf_request,
)
from app.services.auth.browser_session_dependency import (
    get_account_authorization_service,
    get_browser_session_registry,
    get_current_browser_principal,
    get_current_browser_session_identity,
)
from app.services.auth.session_registry import (
    BrowserSessionRegistry,
)
from app.services.security.rbac_policy import (
    MANAGE_BROWSER_SESSIONS,
    VIEW_DASHBOARD,
    VIEW_PATENT_GOVERNANCE,
    VIEW_PATENT_SENSITIVE,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
    get_workspace_context_resolver,
)


application_authorization_logger = logging.getLogger(
    "cgms.application_authorization"
)


MANAGE_MEMORY: Final = "manage_memory"
MANAGE_USERS: Final = "manage_users"
VIEW_AUDIT: Final = "view_audit"
VIEW_SESSIONS: Final = "view_sessions"

CSRF_HEADER_NAME: Final = "X-CSRF-Token"

UNSAFE_METHODS: Final = frozenset(
    {
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }
)

PUBLIC_METHOD_PATHS: Final = frozenset(
    {
        ("GET", "/"),
        ("GET", "/auth/login"),
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
    }
)

BROWSER_ONLY_METHOD_PATHS: Final = frozenset(
    {
        ("GET", "/auth/csrf"),
        ("GET", "/dashboard"),
        ("GET", "/operator"),
        (
            "GET",
            "/product-readiness/dashboard",
        ),
        (
            "GET",
            "/patent-readiness/dashboard",
        ),
        (
            "GET",
            "/patent-readiness/evidence-package",
        ),
        ("GET", "/progress"),
        (
            "POST",
            "/admin/browser-sessions/revoke-user",
        ),
    }
)

BEARER_ONLY_METHOD_PATHS: Final = frozenset(
    {
        ("GET", "/audit/records"),
        ("GET", "/session/history"),
    }
)

BEARER_ONLY_PATH_PREFIXES: Final = (
    "/adapters/",
    "/ingest/",
)

BEARER_ONLY_EXACT_PATHS: Final = frozenset(
    {
        "/memory/event",
        "/memory/hook",
    }
)

CSRF_EXEMPT_BROWSER_MUTATIONS: Final = frozenset(
    {
        (
            "POST",
            "/admin/browser-sessions/revoke-user",
        ),
    }
)

READ_PERMISSION_EXCEPTIONS: Final = {
    "/audit/records": VIEW_AUDIT,
    "/session/history": VIEW_SESSIONS,
    "/patent-readiness/dashboard": (
        VIEW_PATENT_GOVERNANCE
    ),
    "/patent-readiness/evidence-package": (
        VIEW_PATENT_SENSITIVE
    ),
}

MUTATION_PERMISSION_RULES: Final = (
    (
        MANAGE_BROWSER_SESSIONS,
        (
            "/admin/browser-sessions/",
        ),
    ),
    (
        MANAGE_MEMORY,
        (
            "/dashboard/memory/",
            "/dashboard/tasks/",
            "/memory/",
            "/operator/action",
            "/workspace/context",
        ),
    ),
    (
        MANAGE_USERS,
        (
            "/connectors/",
            "/adapters/",
            "/ingest/",
            "/commercial/plan",
            "/ops/errors",
            "/runtime/",
            "/workspace/admin/",
            "/workspace/quotas/",
            "/workspaces",
        ),
    ),
)


class ApplicationAuthorizationPolicyError(
    RuntimeError
):
    """
    Raised when a state-changing route has no governed
    permission mapping.
    """


def _normalize_method(
    method: str,
) -> str:
    normalized = (
        method.strip().upper()
        if isinstance(method, str)
        else ""
    )

    if normalized == "HEAD":
        return "GET"

    return normalized


def _normalize_path(
    path: str,
) -> str:
    normalized = (
        path.strip()
        if isinstance(path, str)
        else ""
    )

    if not normalized.startswith("/"):
        raise ApplicationAuthorizationPolicyError(
            "A canonical application route path is required."
        )

    return normalized


def required_permission_for_route(
    method: str,
    path: str,
) -> str | None:
    """
    Resolve the existing canonical permission required for a
    registered application method and path.

    None represents an explicitly public route. Unknown safe
    reads require dashboard access. Unknown unsafe routes fail
    closed until a mutation permission is assigned.
    """
    normalized_method = _normalize_method(
        method
    )

    normalized_path = _normalize_path(
        path
    )

    if normalized_method == "OPTIONS":
        return None

    if (
        normalized_method,
        normalized_path,
    ) in PUBLIC_METHOD_PATHS:
        return None

    if normalized_method in UNSAFE_METHODS:
        for (
            permission,
            prefixes,
        ) in MUTATION_PERMISSION_RULES:
            if any(
                normalized_path.startswith(
                    prefix
                )
                for prefix in prefixes
            ):
                return permission

        raise ApplicationAuthorizationPolicyError(
            "Unsafe application route has no governed "
            "permission mapping."
        )

    return READ_PERMISSION_EXCEPTIONS.get(
        normalized_path,
        VIEW_DASHBOARD,
    )


def required_transport_for_route(
    method: str,
    path: str,
) -> str:
    """
    Resolve the authentication transport permitted for a
    registered application method and path.

    Public routes perform no authentication. Browser-only and
    bearer-only routes preserve established transport
    boundaries. All remaining protected routes accept either
    transport without fallback from an explicitly supplied
    Authorization header.
    """
    normalized_method = _normalize_method(
        method
    )

    normalized_path = _normalize_path(
        path
    )

    route_identity = (
        normalized_method,
        normalized_path,
    )

    if (
        normalized_method == "OPTIONS"
        or route_identity
        in PUBLIC_METHOD_PATHS
    ):
        return "public"

    if (
        route_identity
        in BROWSER_ONLY_METHOD_PATHS
    ):
        return "browser"

    if (
        route_identity
        in BEARER_ONLY_METHOD_PATHS
        or normalized_path
        in BEARER_ONLY_EXACT_PATHS
        or any(
            normalized_path.startswith(
                prefix
            )
            for prefix
            in BEARER_ONLY_PATH_PREFIXES
        )
    ):
        return "bearer"

    return "dual"


def _route_template(
    request: Request,
) -> str:
    route = request.scope.get(
        "route"
    )

    canonical_path = getattr(
        route,
        "path",
        None,
    )

    if (
        isinstance(canonical_path, str)
        and canonical_path.strip()
    ):
        return canonical_path.strip()

    raw_path = request.url.path

    if (
        isinstance(raw_path, str)
        and raw_path.strip()
    ):
        return raw_path.strip()

    raise ApplicationAuthorizationPolicyError(
        "Application route identity is unavailable."
    )


def _browser_transport_denied(
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Browser session authentication required."
        ),
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


def _permission_denied(
    permission: str,
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Permission denied: "
            f"{permission}"
        ),
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


def _policy_denied() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Application authorization policy "
            "denied the request."
        ),
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


def _csrf_denied() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "The authenticated browser request "
            "could not be validated."
        ),
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


def _require_principal_permission(
    principal: AuthenticatedPrincipal,
    *,
    permission: str,
    transport: str,
) -> None:
    if principal.has_permission(
        permission
    ):
        application_authorization_logger.info(
            "application_authorization_granted "
            "user_id=%s role=%s permission=%s "
            "transport=%s token_id=%s",
            principal.user_id,
            principal.role,
            permission,
            transport,
            principal.token_id
            or "not-recorded",
        )

        return

    application_authorization_logger.warning(
        "application_authorization_denied "
        "user_id=%s role=%s permission=%s "
        "transport=%s token_id=%s",
        principal.user_id,
        principal.role,
        permission,
        transport,
        principal.token_id
        or "not-recorded",
    )

    raise _permission_denied(
        permission
    )


def enforce_application_authorization(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
    authorization_service: Annotated[
        AccountAuthorizationService,
        Depends(
            get_account_authorization_service
        ),
    ],
    workspace_context_resolver: Annotated[
        WorkspaceContextResolver,
        Depends(
            get_workspace_context_resolver
        ),
    ],
) -> AuthenticatedPrincipal | None:
    """
    Enforce the governed application-wide authorization policy.

    An explicitly supplied Authorization header selects Bearer
    authentication and never falls back to a browser cookie.

    Requests without an Authorization header must present a
    valid persistent browser session whose current account and
    role state are revalidated from the database.

    Browser-authenticated unsafe requests additionally require
    signed double-submit CSRF validation unless the route already
    performs an equivalent internal CSRF check.
    """
    try:
        canonical_path = _route_template(
            request
        )

        permission = required_permission_for_route(
            request.method,
            canonical_path,
        )

    except ApplicationAuthorizationPolicyError:
        application_authorization_logger.error(
            "application_authorization_denied "
            "method=%s path=%s reason=policy_unmapped",
            request.method,
            request.url.path,
        )

        raise _policy_denied()

    if permission is None:
        return None

    normalized_method = _normalize_method(
        request.method
    )

    transport_policy = required_transport_for_route(
        normalized_method,
        canonical_path,
    )

    authorization_header = request.headers.get(
        "authorization"
    )

    if (
        transport_policy == "browser"
        and authorization_header is not None
    ):
        application_authorization_logger.warning(
            "application_authorization_denied "
            "method=%s path=%s "
            "reason=browser_transport_required",
            normalized_method,
            canonical_path,
        )

        raise _browser_transport_denied()

    use_bearer_transport = (
        transport_policy == "bearer"
        or (
            transport_policy == "dual"
            and authorization_header is not None
        )
    )

    if use_bearer_transport:
        principal = get_current_principal(
            credentials=credentials,
            authorization_service=(
                authorization_service
            ),
            workspace_context_resolver=(
                workspace_context_resolver
            ),
        )

        _require_principal_permission(
            principal,
            permission=permission,
            transport="bearer",
        )

        return principal

    identity = get_current_browser_session_identity(
        request,
        session_registry,
    )

    principal = get_current_browser_principal(
        request=request,
        identity=identity,
        authorization_service=(
            authorization_service
        ),
        session_registry=session_registry,
        workspace_context_resolver=(
            workspace_context_resolver
        ),
    )

    _require_principal_permission(
        principal,
        permission=permission,
        transport="browser",
    )

    if (
        normalized_method in UNSAFE_METHODS
        and (
            normalized_method,
            canonical_path,
        )
        not in CSRF_EXEMPT_BROWSER_MUTATIONS
    ):
        submitted_token = request.headers.get(
            CSRF_HEADER_NAME
        )

        try:
            validate_browser_csrf_request(
                request,
                submitted_token=(
                    submitted_token
                ),
            )

        except BrowserCsrfValidationError:
            application_authorization_logger.warning(
                "application_authorization_denied "
                "user_id=%s role=%s permission=%s "
                "transport=browser reason=csrf_invalid "
                "method=%s path=%s token_id=%s",
                principal.user_id,
                principal.role,
                permission,
                normalized_method,
                canonical_path,
                principal.token_id
                or "not-recorded",
            )

            raise _csrf_denied()

    return principal
