from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.user import User
from app.services.auth.security import hash_password, verify_password

router = APIRouter()


# -----------------------------
# SIGNUP
# -----------------------------
@router.post("/signup")
def signup(email: str, password: str):
    session = SessionLocal()

    try:
        existing = session.exec(
            select(User).where(User.email == email)
        ).first()

        if existing:
            return {"error": "User already exists"}

        user = User(
            email=email,
            password=hash_password(password)
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return {"message": "User created", "user_id": user.id}

    finally:
        session.close()


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
def login(email: str, password: str):
    session = SessionLocal()

    try:
        user = session.exec(
            select(User).where(User.email == email)
        ).first()

        if not user or not verify_password(password, user.password):
            return {"error": "Invalid credentials"}

        return {
            "message": "Login successful",
            "user_id": user.id
        }

    finally:
        session.close()