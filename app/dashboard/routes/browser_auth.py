from __future__ import annotations

import logging
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)

from fastapi.templating import Jinja2Templates

from app.services.auth.browser_csrf import (
    BrowserCsrfValidationError,
    clear_browser_csrf_cookie,
    issue_browser_csrf_token,
    set_browser_csrf_cookie,
    validate_browser_csrf_request,
)
from app.services.auth.browser_session import (
    clear_browser_session_cookie,
    decode_browser_session_token,
    get_browser_session_token,
    issue_browser_session_token,
    set_browser_session_cookie,
)
from app.services.auth.browser_session_dependency import (
    get_browser_session_registry,
    get_current_browser_principal,
)

from app.services.auth.credential_service import (
    AccountRoleConfigurationError,
    CredentialAuthenticationService,
    InvalidCredentialsError,
)
from app.services.auth.login_throttle import (
    BrowserLoginSecurityService,
    LoginThrottleConfigurationError,
    LoginThrottleDecision,
    LoginThrottlePersistenceError,
)
from app.services.auth.session_registry import (
    BrowserSessionExpiredError,
    BrowserSessionNotRegisteredError,
    BrowserSessionRecordMismatchError,
    BrowserSessionRegistry,
    BrowserSessionRegistryError,
    BrowserSessionRevokedError,
)


router = APIRouter(
    prefix="/auth",
    tags=["browser-authentication"],
)

templates = Jinja2Templates(
    directory="app/dashboard/templates"
)

authentication_logger = logging.getLogger(
    "cgms.security.browser_routes"
)

LOGIN_PATH = "/auth/login"
LOGOUT_PATH = "/auth/logout"

AUTHENTICATED_REDIRECT_PATH = (
    "/patent-readiness/dashboard"
)

MAX_FORM_BODY_BYTES = 16 * 1024
MAX_FORM_FIELDS = 10

FORM_CONTENT_TYPE = (
    "application/x-www-form-urlencoded"
)

GENERIC_LOGIN_ERROR = (
    "Invalid email or password."
)

GENERIC_REQUEST_ERROR = (
    "The request could not be validated. "
    "Please try again."
)

GENERIC_SESSION_ERROR = (
    "Authentication could not be completed. "
    "Please try again."
)

GENERIC_THROTTLE_ERROR = (
    "Too many sign-in attempts. "
    "Please wait and try again."
)


class BrowserFormValidationError(ValueError):
    """
    Raised when a browser-authentication form is malformed,
    oversized or uses an unsupported content type.
    """


def get_credential_authentication_service(
) -> CredentialAuthenticationService:
    return CredentialAuthenticationService()


def get_browser_login_security_service(
) -> BrowserLoginSecurityService:
    return BrowserLoginSecurityService()


def _apply_browser_security_headers(
    response: Response,
) -> Response:
    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Cross-Origin-Opener-Policy"
    ] = "same-origin"

    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'none'; "
        "style-src 'unsafe-inline'; "
        "form-action 'self'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'"
    )

    return response


def _render_login_page(
    request: Request,
    *,
    error_message: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    csrf_token = issue_browser_csrf_token()

    response = templates.TemplateResponse(
        "browser_login.html",
        {
            "request": request,
            "csrf_token": csrf_token,
            "error_message": error_message,
        },
        status_code=status_code,
    )

    set_browser_csrf_cookie(
        response,
        csrf_token,
    )

    _apply_browser_security_headers(
        response
    )

    return response


def _render_throttled_login_page(
    request: Request,
    *,
    decision: LoginThrottleDecision,
) -> HTMLResponse:
    response = _render_login_page(
        request,
        error_message=GENERIC_THROTTLE_ERROR,
        status_code=(
            status.HTTP_429_TOO_MANY_REQUESTS
        ),
    )

    response.headers["Retry-After"] = str(
        max(
            1,
            decision.retry_after_seconds,
        )
    )

    return response


def _render_login_security_failure(
    request: Request,
) -> HTMLResponse:
    return _render_login_page(
        request,
        error_message=GENERIC_SESSION_ERROR,
        status_code=(
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )


def _invalid_request_response() -> HTMLResponse:
    response = HTMLResponse(
        content=(
            "<!doctype html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"utf-8\">"
            "<meta name=\"viewport\" "
            "content=\"width=device-width,"
            "initial-scale=1\">"
            "<title>Invalid Request</title>"
            "</head>"
            "<body>"
            "<main>"
            "<h1>Invalid request</h1>"
            "<p>"
            "The request could not be validated."
            "</p>"
            "</main>"
            "</body>"
            "</html>"
        ),
        status_code=(
            status.HTTP_400_BAD_REQUEST
        ),
    )

    _apply_browser_security_headers(
        response
    )

    return response


def _session_revocation_failure_response(
) -> HTMLResponse:
    """
    Return a fail-closed response when server-side session
    revocation cannot be completed.

    Local browser cookies are still removed so the browser
    cannot continue using the affected session.
    """
    response = HTMLResponse(
        content=(
            "<!doctype html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"utf-8\">"
            "<meta name=\"viewport\" "
            "content=\"width=device-width,"
            "initial-scale=1\">"
            "<title>Logout Incomplete</title>"
            "</head>"
            "<body>"
            "<main>"
            "<h1>Logout could not be completed</h1>"
            "<p>"
            "The server could not invalidate the "
            "current session. Please try again."
            "</p>"
            "</main>"
            "</body>"
            "</html>"
        ),
        status_code=(
            status.HTTP_503_SERVICE_UNAVAILABLE
        ),
    )

    clear_browser_session_cookie(
        response
    )

    clear_browser_csrf_cookie(
        response
    )

    _apply_browser_security_headers(
        response
    )

    return response


async def _parse_urlencoded_form(
    request: Request,
) -> dict[str, list[str]]:
    raw_content_type = request.headers.get(
        "content-type",
        "",
    )

    content_type = (
        raw_content_type
        .split(";", maxsplit=1)[0]
        .strip()
        .lower()
    )

    if content_type != FORM_CONTENT_TYPE:
        raise BrowserFormValidationError(
            "Unsupported form content type."
        )

    content_length = request.headers.get(
        "content-length"
    )

    if content_length:
        try:
            declared_length = int(
                content_length
            )

        except ValueError as exc:
            raise BrowserFormValidationError(
                "Invalid content length."
            ) from exc

        if (
            declared_length < 0
            or declared_length
            > MAX_FORM_BODY_BYTES
        ):
            raise BrowserFormValidationError(
                "Form body is too large."
            )

    body = await request.body()

    if len(body) > MAX_FORM_BODY_BYTES:
        raise BrowserFormValidationError(
            "Form body is too large."
        )

    try:
        decoded_body = body.decode(
            "utf-8",
            errors="strict",
        )

    except UnicodeDecodeError as exc:
        raise BrowserFormValidationError(
            "Form body is not valid UTF-8."
        ) from exc

    try:
        return parse_qs(
            decoded_body,
            keep_blank_values=True,
            strict_parsing=False,
            max_num_fields=MAX_FORM_FIELDS,
        )

    except ValueError as exc:
        raise BrowserFormValidationError(
            "Form body is invalid."
        ) from exc


def _single_form_value(
    form_data: dict[str, list[str]],
    field_name: str,
) -> str:
    values = form_data.get(
        field_name
    )

    if (
        values is None
        or len(values) != 1
        or not isinstance(values[0], str)
    ):
        raise BrowserFormValidationError(
            f"Invalid form field: {field_name}."
        )

    return values[0]


@router.get(
    "/login",
    response_class=HTMLResponse,
    response_model=None,
    name="browser_login_page",
)
def browser_login_page(
    request: Request,
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
) -> Response:
    """
    Render the browser login page.

    An existing browser cookie causes an authenticated redirect
    only when both the JWT and persistent registry record are
    active. Stale or revoked cookies are cleared.
    """
    existing_token = (
        get_browser_session_token(
            request
        )
    )

    if existing_token:
        identity = (
            decode_browser_session_token(
                existing_token
            )
        )

        if identity is not None:
            try:
                session_registry.require_active(
                    identity
                )

            except BrowserSessionRegistryError:
                authentication_logger.info(
                    "browser_login_session_rejected "
                    "user_id=%s token_id=%s "
                    "reason=session_not_active",
                    identity.user_id,
                    identity.token_id,
                )

            else:
                response = RedirectResponse(
                    url=(
                        AUTHENTICATED_REDIRECT_PATH
                    ),
                    status_code=(
                        status.HTTP_303_SEE_OTHER
                    ),
                )

                _apply_browser_security_headers(
                    response
                )

                return response

    response = _render_login_page(
        request
    )

    if existing_token:
        clear_browser_session_cookie(
            response
        )

    return response


@router.post(
    "/login",
    response_class=HTMLResponse,
    response_model=None,
    name="browser_login_submit",
)
async def browser_login_submit(
    request: Request,
    credential_service: Annotated[
        CredentialAuthenticationService,
        Depends(
            get_credential_authentication_service
        ),
    ],
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
    login_security_service: Annotated[
        BrowserLoginSecurityService,
        Depends(
            get_browser_login_security_service
        ),
    ],
) -> Response:
    """
    Authenticate an account, register the resulting browser
    session and issue the hardened session cookie.

    The browser cookie is not issued unless persistent session
    registration succeeds.
    """
    try:
        network_identifier = (
            login_security_service
            .resolve_network_identifier(
                request
            )
        )
    except LoginThrottleConfigurationError:
        authentication_logger.error(
            "browser_login_denied "
            "reason=throttle_configuration_failed"
        )

        return _render_login_security_failure(
            request
        )

    try:
        form_data = (
            await _parse_urlencoded_form(
                request
            )
        )

        submitted_csrf_token = (
            _single_form_value(
                form_data,
                "csrf_token",
            )
        )

        validate_browser_csrf_request(
            request,
            submitted_token=(
                submitted_csrf_token
            ),
        )

        email = _single_form_value(
            form_data,
            "email",
        )

        password = _single_form_value(
            form_data,
            "password",
        )

    except (
        BrowserFormValidationError,
        BrowserCsrfValidationError,
    ):
        authentication_logger.warning(
            "browser_login_denied "
            "reason=invalid_request"
        )

        try:
            decision = (
                login_security_service
                .record_invalid_request(
                    network_identifier=(
                        network_identifier
                    )
                )
            )
        except (
            LoginThrottleConfigurationError,
            LoginThrottlePersistenceError,
        ):
            authentication_logger.error(
                "browser_login_denied "
                "reason=throttle_record_failed"
            )

            return _render_login_security_failure(
                request
            )

        if decision.blocked:
            return _render_throttled_login_page(
                request,
                decision=decision,
            )

        return _render_login_page(
            request,
            error_message=GENERIC_REQUEST_ERROR,
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
        )

    try:
        decision = (
            login_security_service.check(
                email=email,
                network_identifier=(
                    network_identifier
                ),
            )
        )
    except (
        LoginThrottleConfigurationError,
        LoginThrottlePersistenceError,
    ):
        authentication_logger.error(
            "browser_login_denied "
            "reason=throttle_check_failed"
        )

        return _render_login_security_failure(
            request
        )

    if decision.blocked:
        authentication_logger.warning(
            "browser_login_denied "
            "reason=throttled"
        )

        return _render_throttled_login_page(
            request,
            decision=decision,
        )

    try:
        account = (
            credential_service.authenticate(
                email=email,
                password=password,
            )
        )

    except (
        InvalidCredentialsError,
        AccountRoleConfigurationError,
    ):
        authentication_logger.warning(
            "browser_login_denied "
            "reason=authentication_failed"
        )

        try:
            decision = (
                login_security_service
                .record_failure(
                    email=email,
                    network_identifier=(
                        network_identifier
                    ),
                )
            )
        except (
            LoginThrottleConfigurationError,
            LoginThrottlePersistenceError,
        ):
            authentication_logger.error(
                "browser_login_denied "
                "reason=throttle_record_failed"
            )

            return _render_login_security_failure(
                request
            )

        if decision.blocked:
            return _render_throttled_login_page(
                request,
                decision=decision,
            )

        return _render_login_page(
            request,
            error_message=GENERIC_LOGIN_ERROR,
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
        )

    session_token = (
        issue_browser_session_token(
            account
        )
    )

    session_identity = (
        decode_browser_session_token(
            session_token
        )
    )

    if session_identity is None:
        authentication_logger.error(
            "browser_login_denied "
            "user_id=%s "
            "reason=session_token_validation_failed",
            account.user_id,
        )

        return _render_login_page(
            request,
            error_message=GENERIC_SESSION_ERROR,
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )

    try:
        session_registry.register(
            session_identity
        )

    except BrowserSessionRegistryError:
        authentication_logger.error(
            "browser_login_denied "
            "user_id=%s token_id=%s "
            "reason=session_registration_failed",
            account.user_id,
            session_identity.token_id,
        )

        return _render_login_page(
            request,
            error_message=GENERIC_SESSION_ERROR,
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )

    try:
        login_security_service.record_success(
            email=email,
            network_identifier=(
                network_identifier
            ),
            user_id=account.user_id,
        )
    except (
        LoginThrottleConfigurationError,
        LoginThrottlePersistenceError,
    ):
        authentication_logger.error(
            "browser_login_denied "
            "user_id=%s token_id=%s "
            "reason=login_audit_failed",
            account.user_id,
            session_identity.token_id,
        )

        try:
            session_registry.revoke(
                session_identity,
                reason="login_audit_failure",
                revoked_by_user_id=(
                    account.user_id
                ),
            )
        except BrowserSessionRegistryError:
            authentication_logger.critical(
                "browser_login_cleanup_failed "
                "user_id=%s token_id=%s "
                "reason=session_revocation_failed",
                account.user_id,
                session_identity.token_id,
            )

        return _render_login_security_failure(
            request
        )

    response = RedirectResponse(
        url=AUTHENTICATED_REDIRECT_PATH,
        status_code=(
            status.HTTP_303_SEE_OTHER
        ),
    )

    set_browser_session_cookie(
        response,
        session_token,
    )

    # The pre-authentication CSRF token is single-use.
    # Protected browser pages will issue a fresh token for
    # subsequent state-changing operations.
    clear_browser_csrf_cookie(
        response
    )

    _apply_browser_security_headers(
        response
    )

    authentication_logger.info(
        "browser_login_granted "
        "user_id=%s role=%s token_id=%s",
        account.user_id,
        account.canonical_role,
        session_identity.token_id,
    )

    return response

@router.get(
    "/csrf",
    response_class=JSONResponse,
    response_model=None,
    name="browser_authenticated_csrf",
)
def browser_authenticated_csrf(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            get_current_browser_principal
        ),
    ],
) -> JSONResponse:
    """
    Issue a fresh signed CSRF token for an authenticated browser
    session.

    The endpoint requires the full browser-session security
    chain: signed cookie validation, persistent session-registry
    validation and current database-backed authorization.
    """
    csrf_token = issue_browser_csrf_token()

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "csrf_token": csrf_token,
        },
    )

    set_browser_csrf_cookie(
        response,
        csrf_token,
    )

    _apply_browser_security_headers(
        response
    )

    authentication_logger.info(
        "browser_csrf_issued "
        "user_id=%s role=%s token_id=%s",
        principal.user_id,
        principal.role,
        principal.token_id
        or "not-recorded",
    )

    return response

@router.post(
    "/logout",
    response_class=HTMLResponse,
    response_model=None,
    name="browser_logout",
)
async def browser_logout(
    request: Request,
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
) -> Response:
    """
    Revoke the current persistent session and clear the browser
    authentication and CSRF cookies.

    Logout remains idempotent for already revoked, expired,
    unregistered or otherwise stale session cookies.
    """
    try:
        form_data = (
            await _parse_urlencoded_form(
                request
            )
        )

        submitted_csrf_token = (
            _single_form_value(
                form_data,
                "csrf_token",
            )
        )

        validate_browser_csrf_request(
            request,
            submitted_token=(
                submitted_csrf_token
            ),
        )

    except (
        BrowserFormValidationError,
        BrowserCsrfValidationError,
    ):
        authentication_logger.warning(
            "browser_logout_denied "
            "reason=invalid_request"
        )

        return _invalid_request_response()

    session_token = (
        get_browser_session_token(
            request
        )
    )

    if session_token:
        identity = (
            decode_browser_session_token(
                session_token
            )
        )

        if identity is not None:
            try:
                session_registry.revoke(
                    identity,
                    reason="logout",
                    revoked_by_user_id=(
                        identity.user_id
                    ),
                )

            except (
                BrowserSessionNotRegisteredError,
                BrowserSessionRevokedError,
                BrowserSessionExpiredError,
                BrowserSessionRecordMismatchError,
            ):
                # Logout remains idempotent for stale,
                # previously revoked, expired or legacy
                # unregistered cookies.
                authentication_logger.info(
                    "browser_logout_session_absent "
                    "user_id=%s token_id=%s",
                    identity.user_id,
                    identity.token_id,
                )

            except BrowserSessionRegistryError:
                authentication_logger.error(
                    "browser_logout_failed "
                    "user_id=%s token_id=%s "
                    "reason=session_revocation_failed",
                    identity.user_id,
                    identity.token_id,
                )

                return (
                    _session_revocation_failure_response()
                )

    response = RedirectResponse(
        url=LOGIN_PATH,
        status_code=(
            status.HTTP_303_SEE_OTHER
        ),
    )

    clear_browser_session_cookie(
        response
    )

    clear_browser_csrf_cookie(
        response
    )

    _apply_browser_security_headers(
        response
    )

    authentication_logger.info(
        "browser_logout_completed"
    )

    return response