from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    deleted = 0

    for m in memories:
        if m.summary in [
            "Clarify objective",
            "Break into steps",
            "Execute first step"
        ]:
            if not m.depends_on:
                print("Deleting:", m.id, m.summary)
                session.delete(m)
                deleted += 1

    session.commit()

    print(f"\n✅ Deleted {deleted} orphan subtasks")

finally:
    session.close()