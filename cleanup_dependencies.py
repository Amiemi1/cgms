from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    for m in memories:
        if m.summary in [
            "Clarify objective",
            "Break into steps",
            "Execute first step"
        ]:
            print("RESETTING:", m.id, m.summary, m.depends_on)
            m.depends_on = None
            session.add(m)

    session.commit()
    print("\n✅ CLEANUP COMPLETE")

finally:
    session.close()