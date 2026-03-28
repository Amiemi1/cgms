from fastapi import FastAPI
from sqlmodel import SQLModel, select
from sqlalchemy import text
import logging

from app.db.session import engine, SessionLocal
from app.db.models.memory import Memory
from app.db.models.user import User

from app.dashboard.auth import router as auth_router


# -----------------------------
# LOGGING
# -----------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# FASTAPI APP
# -----------------------------

app = FastAPI(
    title="CGMS Dashboard API",
    description="Contextual Group Memory System",
    version="1.0"
)


# -----------------------------
# STARTUP EVENT
# -----------------------------

@app.on_event("startup")
def on_startup():

    try:

        logger.info("Creating database tables...")

        SQLModel.metadata.create_all(engine)

        # TEMP FIX: ensure password_hash column exists
        session = SessionLocal()

        try:
            session.exec(
                text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS password_hash TEXT')
            )
            session.commit()
        finally:
            session.close()

        logger.info("Database tables ready.")

    except Exception as e:

        logger.error(f"Startup DB error: {e}")


# -----------------------------
# INCLUDE AUTH ROUTES
# -----------------------------

app.include_router(auth_router)


# -----------------------------
# ROOT CHECK
# -----------------------------

@app.get("/")
def root():

    return {
        "status": "CGMS Dashboard running"
    }


# -----------------------------
# DEBUG: LIST DATABASE TABLES
# -----------------------------

@app.get("/debug/tables")
def debug_tables():

    session = SessionLocal()

    try:

        result = session.exec(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        ).all()

        return result

    finally:

        session.close()


# -----------------------------
# GET USER MEMORIES
# -----------------------------

@app.get("/memories/{user_id}")
def get_memories(user_id: int):

    session = SessionLocal()

    try:

        user = session.get(User, user_id)

        if not user:
            return {"error": "User not found"}

        if not user.chat_id:
            return []

        memories = session.exec(
            select(Memory).where(Memory.chat_id == user.chat_id)
        ).all()

        return [
            {
                "summary": m.summary,
                "priority": m.priority,
                "type": m.memory_type,
                "status": m.status,
            }
            for m in memories
        ]

    finally:

        session.close()


# -----------------------------
# HEALTH CHECK
# -----------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }