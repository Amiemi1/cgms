from sqlmodel import create_engine, Session
from app.core.config import settings

# 🔥 DEBUG — show which DB your app is using
print("APP DATABASE URL:", settings.DATABASE_URL)

# Create engine
engine = create_engine(settings.DATABASE_URL, echo=True)

# Dependency-style session (FastAPI compatible)
def get_session():
    with Session(engine) as session:
        yield session

# Local session (used in services/tests)
def SessionLocal():
    return Session(engine)