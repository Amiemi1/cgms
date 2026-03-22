from fastapi import APIRouter
from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.user import User
from app.services.auth.security import hash_password, verify_password
from app.dashboard.schemas import UserCreate, UserLogin

router = APIRouter()


# -----------------------------
# SIGNUP
# -----------------------------
@router.post("/signup")
def signup(data: UserCreate):
    session = SessionLocal()

    try:
        # 🔍 Check if user already exists
        existing = session.exec(
            select(User).where(User.email == data.email)
        ).first()

        if existing:
            return {"error": "User already exists"}

        # 🔐 Hash password
        hashed_password = hash_password(data.password)

        # 🧠 Create user
        user = User(
            email=data.email,
            password=hashed_password
        )

        session.add(user)
        session.commit()
        session.refresh(user)

        return {
            "message": "User created",
            "user_id": user.id
        }

    except Exception as e:
        return {"error": str(e)}  # 🔥 shows real error

    finally:
        session.close()


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
def login(data: UserLogin):
    session = SessionLocal()

    try:
        # 🔍 Find user
        user = session.exec(
            select(User).where(User.email == data.email)
        ).first()

        if not user:
            return {"error": "User not found"}

        # 🔐 Verify password
        if not verify_password(data.password, user.password):
            return {"error": "Invalid credentials"}

        return {
            "message": "Login successful",
            "user_id": user.id
        }

    except Exception as e:
        return {"error": str(e)}  # 🔥 shows real error

    finally:
        session.close()