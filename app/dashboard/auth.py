from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.user import User

from app.services.auth.security import hash_password, verify_password
from app.services.auth.jwt_handler import create_access_token


router = APIRouter()


# -----------------------------
# REQUEST SCHEMAS
# -----------------------------

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# -----------------------------
# SIGNUP
# -----------------------------

@router.post("/signup")
def signup(data: SignupRequest):

    session = SessionLocal()

    try:

        # Check if user already exists
        existing_user = session.exec(
            select(User).where(User.email == data.email)
        ).first()

        if existing_user:
            return {"error": "user already exists"}

        # Create new user
        new_user = User(
            email=data.email,
            password_hash=hash_password(data.password)
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "message": "User created",
            "user_id": new_user.id
        }

    finally:
        session.close()


# -----------------------------
# LOGIN
# -----------------------------

@router.post("/login")
def login(data: LoginRequest):

    session = SessionLocal()

    try:

        user = session.exec(
            select(User).where(User.email == data.email)
        ).first()

        if not user:
            return {"error": "User not found"}

        if not verify_password(data.password, user.password_hash):
            return {"error": "Invalid password"}

        # Create JWT token
        token = create_access_token(
            {"user_id": user.id}
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    finally:
        session.close()