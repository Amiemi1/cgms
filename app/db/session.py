from sqlmodel import create_engine, Session
from app.core.config import settings


# Create engine
engine = create_engine(settings.DATABASE_URL, echo=True)


# Dependency-style session (FastAPI compatible)
def get_session():
    with Session(engine) as session:
        yield session


# ✅ Add this (CRITICAL for your scheduler)
def SessionLocal():
    return Session(engine)