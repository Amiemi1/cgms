from sqlmodel import Session, create_engine

from app.core.config import settings


# The database URL is intentionally never written to logs.
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,
)


def get_session():
    """
    FastAPI-compatible database session dependency.
    """
    with Session(engine) as session:
        yield session


def SessionLocal():
    """
    Create a database session for services and local workflows.
    """
    return Session(engine)