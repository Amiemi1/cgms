from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    print("\n=== RAW DATABASE STATE ===\n")

    for m in memories:
        print(
            f"ID: {m.id} | "
            f"SUMMARY: {m.summary} | "
            f"STATUS: {m.status} | "
            f"DEPENDS_ON: {m.depends_on}"
        )

finally:
    session.close()