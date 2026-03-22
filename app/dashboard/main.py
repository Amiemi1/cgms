from fastapi import FastAPI
from sqlmodel import Session, select, text
from sqlmodel import SQLModel
from app.db.session import engine

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.user import User
from app.db.models import User, Memory

app = FastAPI()
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


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
        result = session.exec(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        ).all()
        return result
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

    finally:
        session.close()