from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel
from sqlmodel import select

from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.auth.credential_service import (
    AccountRoleConfigurationError,
    CredentialAuthenticationService,
    InvalidCredentialsError,
)
from app.services.auth.jwt_handler import (
    create_access_token,
)
from app.services.auth.security import (
    hash_password,
)
from app.services.workspace.repository import (
    WorkspaceRepositoryError,
)
from app.services.workspace.resolution import (
    WorkspaceContextResolver,
    get_workspace_context_resolver,
)


router = APIRouter()


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_credential_authentication_service(
) -> CredentialAuthenticationService:
    return CredentialAuthenticationService()


def _authentication_denied(
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


@router.post("/signup")
def signup(
    data: SignupRequest,
):
    session = SessionLocal()

    try:
        existing_user = session.exec(
            select(
                User
            ).where(
                User.email
                == data.email
            )
        ).first()

        if existing_user:
            return {
                "error":
                    "user already exists"
            }

        new_user = User(
            email=data.email,
            password_hash=hash_password(
                data.password
            ),
        )

        session.add(
            new_user
        )

        session.commit()
        session.refresh(
            new_user
        )

        return {
            "message": "User created",
            "user_id": new_user.id,
        }

    finally:
        session.close()


@router.post("/login")
def login(
    data: LoginRequest,
    credential_service: Annotated[
        CredentialAuthenticationService,
        Depends(
            get_credential_authentication_service
        ),
    ],
    workspace_context_resolver: Annotated[
        WorkspaceContextResolver,
        Depends(
            get_workspace_context_resolver
        ),
    ],
):
    try:
        account = (
            credential_service.authenticate(
                email=data.email,
                password=data.password,
            )
        )

    except (
        InvalidCredentialsError,
        AccountRoleConfigurationError,
    ):
        raise _authentication_denied()

    try:
        workspace_context = (
            workspace_context_resolver
            .resolve_default(
                account.user_id
            )
        )

    except WorkspaceRepositoryError:
        raise _authentication_denied()

    token = create_access_token(
        {
            "user_id":
                account.user_id,
            "role":
                account.canonical_role,
            "workspace_id":
                workspace_context.workspace_id,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
