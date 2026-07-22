from sqlmodel import Session, create_engine

from app.core.config import settings
from app.core.runtime_policy import (
    get_runtime_environment,
    get_sql_echo_enabled,
)


# The database URL is intentionally never written to logs.
# SQL statement logging is disabled by default and cannot be
# enabled in staging or production.
_runtime_environment = get_runtime_environment()

engine = create_engine(
    settings.DATABASE_URL,
    echo=get_sql_echo_enabled(
        environment=_runtime_environment
    ),
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
