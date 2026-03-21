from app.db.base import SQLModel
from app.db.session import engine

# 🔥 IMPORTANT: import ALL models
from app.db.models.memory import Memory
from app.db.models.candidate_memory import CandidateMemory
from app.db.models.message import Message
from app.db.models.learning import Learning  # ✅ THIS WAS MISSING


def main():
    print("Creating tables...")
    SQLModel.metadata.create_all(engine)
    print("Done.")


if __name__ == "__main__":
    main()