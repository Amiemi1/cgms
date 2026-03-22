from fastapi import FastAPI
from sqlmodel import select, text, SQLModel
from contextlib import asynccontextmanager
import logging

from app.db.session import SessionLocal, engine

# 🔥 IMPORTANT: ensures models are registered
from app.db.models import User, Memory

# 🔥 AUTH ROUTES
from app.dashboard.auth import router as auth_router


# -----------------------------
# LOGGER
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# LIFESPAN (STABLE STARTUP)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("🚀 Starting up application...")
        logger.info("📦 Creating database tables...")

        SQLModel.metadata.create_all(engine)

        logger.info("✅ Tables created successfully")

    except Exception as e:
        logger.error(f"❌ Startup DB error: {e}")

    yield  # keeps app alive


# -----------------------------
# APP INIT
# -----------------------------
app = FastAPI(lifespan=lifespan)


# -----------------------------
# REGISTER ROUTES
# -----------------------------
app.include_router(auth_router)


# -----------------------------
# ROOT CHECK
# -----------------------------
@app.get("/")
def root():
    return {"status": "CGMS Dashboard running"}


# -----------------------------
# DEBUG: LIST TABLES
# -----------------------------
@app.get("/debug/tables")
def debug_tables():
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        ).fetchall()

        return [row[0] for row in result]

    except Exception as e:
        return {"error": str(e)}

    finally:
        session.close()


# -----------------------------
# GET MEMORIES BY USER
# -----------------------------
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
                "type": m.memory_type,
            }
            for m in memories
        ]

    except Exception as e:
        return {"error": str(e)}

    finally:
        session.close()