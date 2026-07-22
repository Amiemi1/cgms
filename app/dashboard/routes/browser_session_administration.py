from __future__ import annotations

from datetime import datetime
from typing import Annotated
from urllib.parse import parse_qs

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from fastapi.responses import JSONResponse

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_csrf import (
    BrowserCsrfValidationError,
    validate_browser_csrf_request,
)
from app.services.auth.browser_session_dependency import (
    require_browser_permission,
)
from app.services.security.rbac_policy import (
    MANAGE_BROWSER_SESSIONS,
)
from app.services.security.session_administration import (
    AdministrativeSessionRevocationResult,
    SessionAdministrationInputError,
    SessionAdministrationPermissionError,
    SessionAdministrationPersistenceError,
    SessionAdministrationService,
)


router = APIRouter(
    prefix="/admin/browser-sessions",
    tags=["browser-session-administration"],
)

FORM_CONTENT_TYPE = (
    "application/x-www-form-urlencoded"
)

MAX_FORM_BODY_BYTES = 4 * 1024
MAX_FORM_FIELDS = 5

DEFAULT_REVOCATION_REASON = (
    "admin_revocation"
)

GENERIC_REQUEST_ERROR = (
    "The session revocation request could not be validated."
)

GENERIC_PERMISSION_ERROR = (
    "Administrative session permission is required."
)

GENERIC_PERSISTENCE_ERROR = (
    "Session revocation could not be completed."
)


class SessionAdministrationFormError(
    ValueError
):
    """
    Raised when the administrative session-revocation form is
    malformed, oversized or structurally invalid.
    """


def get_session_administration_service(
) -> SessionAdministrationService:
    return SessionAdministrationService()


def _security_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    }


def _json_response(
    *,
    status_code: int,
    payload: dict[str, object],
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=_security_headers(),
    )


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
        raise SessionAdministrationFormError(
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
            raise SessionAdministrationFormError(
                "Invalid content length."
            ) from exc

        if (
            declared_length < 0
            or declared_length
            > MAX_FORM_BODY_BYTES
        ):
            raise SessionAdministrationFormError(
                "Form body is too large."
            )

    body = await request.body()

    if len(body) > MAX_FORM_BODY_BYTES:
        raise SessionAdministrationFormError(
            "Form body is too large."
        )

    try:
        decoded_body = body.decode(
            "utf-8",
            errors="strict",
        )

    except UnicodeDecodeError as exc:
        raise SessionAdministrationFormError(
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
        raise SessionAdministrationFormError(
            "Form body is invalid."
        ) from exc


def _required_single_value(
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
        or not values[0].strip()
    ):
        raise SessionAdministrationFormError(
            f"Invalid form field: {field_name}."
        )

    return values[0].strip()


def _optional_single_value(
    form_data: dict[str, list[str]],
    field_name: str,
    *,
    default: str,
) -> str:
    values = form_data.get(
        field_name
    )

    if values is None:
        return default

    if (
        len(values) != 1
        or not isinstance(values[0], str)
    ):
        raise SessionAdministrationFormError(
            f"Invalid form field: {field_name}."
        )

    normalized = values[0].strip()

    return normalized or default


def _success_payload(
    result: AdministrativeSessionRevocationResult,
) -> dict[str, object]:
    revoked_at: datetime = result.revoked_at

    return {
        "status": "completed",
        "target_user_id": result.target_user_id,
        "revoked_count": result.revoked_count,
        "reason": result.reason,
        "revoked_at": revoked_at.isoformat(),
    }


@router.post(
    "/revoke-user",
    response_class=JSONResponse,
    response_model=None,
    name="revoke_user_browser_sessions",
)
async def revoke_user_browser_sessions(
    request: Request,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            require_browser_permission(
                MANAGE_BROWSER_SESSIONS
            )
        ),
    ],
    administration_service: Annotated[
        SessionAdministrationService,
        Depends(
            get_session_administration_service
        ),
    ],
) -> JSONResponse:
    """
    Revoke every active browser session belonging to a target
    account.

    The authenticated actor must possess the explicit
    manage_browser_sessions permission. The request must also
    pass signed double-submit CSRF validation.
    """
    try:
        form_data = await _parse_urlencoded_form(
            request
        )

        submitted_csrf_token = (
            _required_single_value(
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

        target_user_id = (
            _required_single_value(
                form_data,
                "target_user_id",
            )
        )

        reason = _optional_single_value(
            form_data,
            "reason",
            default=(
                DEFAULT_REVOCATION_REASON
            ),
        )

    except (
        SessionAdministrationFormError,
        BrowserCsrfValidationError,
    ):
        return _json_response(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            payload={
                "detail": GENERIC_REQUEST_ERROR,
            },
        )

    try:
        result = (
            administration_service
            .revoke_user_sessions(
                actor=principal,
                target_user_id=(
                    target_user_id
                ),
                reason=reason,
            )
        )

    except SessionAdministrationInputError:
        return _json_response(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            payload={
                "detail": GENERIC_REQUEST_ERROR,
            },
        )

    except SessionAdministrationPermissionError:
        return _json_response(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            payload={
                "detail": GENERIC_PERMISSION_ERROR,
            },
        )

    except SessionAdministrationPersistenceError:
        return _json_response(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            payload={
                "detail": GENERIC_PERSISTENCE_ERROR,
            },
        )

    return _json_response(
        status_code=status.HTTP_200_OK,
        payload=_success_payload(
            result
        ),
    )