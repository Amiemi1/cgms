from __future__ import annotations

from typing import Annotated
from urllib.parse import urlsplit

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel

from app.services.auth.auth_dependency import (
    AuthenticatedPrincipal,
)
from app.services.auth.browser_session import (
    BrowserSessionIdentity,
)
from app.services.auth.browser_session_dependency import (
    get_browser_session_registry,
    get_current_browser_principal,
    get_current_browser_session_identity,
)
from app.services.auth.session_registry import (
    BrowserSessionRegistry,
    BrowserSessionRegistryError,
)
from app.services.workspace.repository import (
    WorkspaceRepositoryError,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
    get_workspace_context_resolver,
)


router = APIRouter()


class WorkspaceSwitchPayload(BaseModel):
    workspace_id: str
    redirect_to: str | None = None


def _safe_redirect_target(
    value: str | None,
) -> str:
    fallback = "/dashboard"

    if not isinstance(value, str):
        return fallback

    candidate = value.strip()

    if (
        not candidate.startswith("/")
        or candidate.startswith("//")
        or "\\" in candidate
        or any(
            ord(character) < 32
            for character in candidate
        )
    ):
        return fallback

    parsed = urlsplit(candidate)

    if parsed.scheme or parsed.netloc:
        return fallback

    return candidate


@router.get(
    "/workspace/context"
)
def context(
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            get_current_browser_principal
        ),
    ],
) -> dict[str, str]:
    return {
        "workspace_id": principal.workspace_id,
    }


@router.post(
    "/workspace/context"
)
def switch(
    payload: WorkspaceSwitchPayload,
    principal: Annotated[
        AuthenticatedPrincipal,
        Depends(
            get_current_browser_principal
        ),
    ],
    identity: Annotated[
        BrowserSessionIdentity,
        Depends(
            get_current_browser_session_identity
        ),
    ],
    session_registry: Annotated[
        BrowserSessionRegistry,
        Depends(
            get_browser_session_registry
        ),
    ],
    workspace_context_resolver: Annotated[
        WorkspaceContextResolver,
        Depends(
            get_workspace_context_resolver
        ),
    ],
) -> dict[str, str]:
    workspace_id = payload.workspace_id

    try:
        resolved = (
            workspace_context_resolver
            .resolve_requested(
                user_id=principal.user_id,
                workspace_id=workspace_id,
            )
        )

        session_state = (
            session_registry.set_workspace(
                identity,
                workspace_id=(
                    resolved.workspace_id
                ),
            )
        )

    except WorkspaceRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "The requested workspace selection "
                "is not available."
            ),
        ) from exc

    except BrowserSessionRegistryError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "The authenticated browser session "
                "is not available."
            ),
        ) from exc

    return {
        "workspace_id": session_state.workspace_id,
        "redirect_to": _safe_redirect_target(
            payload.redirect_to
        ),
    }
