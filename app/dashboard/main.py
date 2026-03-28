import logging

from fastapi import FastAPI
from sqlmodel import SQLModel, select, text

from app.db.session import engine, SessionLocal
from app.db.models.memory import Memory
from app.db.models.user import User

from app.dashboard.auth import router as auth_router


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(title="CGMS Dashboard")


# --------------------------------------------------
# Database Startup
# --------------------------------------------------

@app.on_event("startup")
def on_startup():

    try:

        logger.info("Initializing database...")

        SQLModel.metadata.create_all(engine)

        session = SessionLocal()

        try:

            # --------------------------------
            # Fix USER table schema mismatch
            # --------------------------------

            session.exec(
                text(
                    """
                    ALTER TABLE "user"
                    ADD COLUMN IF NOT EXISTS password_hash TEXT
                    """
                )
            )

            session.exec(
                text(
                    """
                    ALTER TABLE "user"
                    DROP COLUMN IF EXISTS password
                    """
                )
            )

            session.commit()

            logger.info("Database schema validated")

        finally:
            session.close()

    except Exception as e:

        logger.error(f"Startup DB error: {e}")


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(auth_router)


# --------------------------------------------------
# Root Check
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "status": "CGMS Dashboard running"
    }


# --------------------------------------------------
# Debug: List Tables
# --------------------------------------------------

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


# --------------------------------------------------
# Get Memories for User
# --------------------------------------------------

@app.get("/memories/{user_id}")
def get_memories(user_id: int):

    session = SessionLocal()

    try:

        user = session.get(User, user_id)

        if not user or not user.chat_id:
            return []

        memories = session.exec(
            select(Memory).where(Memory.chat_id == user.chat_id)
        ).all()

        return [
            {
                "summary": m.summary,
                "priority": m.priority,
                "type": m.memory_type
            }
            for m in memories
        ]

    finally:
        session.close()