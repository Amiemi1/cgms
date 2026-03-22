from sqlmodel import SQLModel
from app.db.session import engine

# 🔥 IMPORTANT: import models so SQLModel sees them
from app.db.models import User, Memory


def init_db():
    SQLModel.metadata.create_all(engine)