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
    RedirectResponse,
    Response,
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
from app.services.auth.credential_service import (
    AccountRoleConfigurationError,
    CredentialAuthenticationService,
    InvalidCredentialsError,
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


class BrowserFormValidationError(ValueError):
    """
    Raised when a browser-authentication form is malformed,
    oversized or uses an unsupported content type.
    """


def get_credential_authentication_service(
) -> CredentialAuthenticationService:
    return CredentialAuthenticationService()


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
) -> Response:
    
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
            response = RedirectResponse(
                url=AUTHENTICATED_REDIRECT_PATH,
                status_code=(
                    status.HTTP_303_SEE_OTHER
                ),
            )

            _apply_browser_security_headers(
                response
            )

            return response

    return _render_login_page(
        request
    )


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
) -> Response:
    
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

        return _render_login_page(
            request,
            error_message=GENERIC_REQUEST_ERROR,
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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
        "user_id=%s role=%s",
        account.user_id,
        account.canonical_role,
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
) -> Response:
    
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