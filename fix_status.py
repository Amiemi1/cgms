from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    print("\n--- FIXING STATUSES ---")

    for m in memories:
        if m.summary in [
            "Draft key points",
            "Align data and evidence",
            "Review and refine messaging"
        ]:
            print(f"Updating: {m.id} | {m.summary}")
            m.status = "completed"
            session.add(m)

    session.commit()
    print("✅ Done")

finally:
    session.close()