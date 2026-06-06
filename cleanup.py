from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    for m in memories:
        if m.summary == "Distributor meeting Friday":
            print("FIXING:", m.id, m.summary, m.depends_on)
            m.depends_on = None
            session.add(m)

    session.commit()

    print("DONE")

finally:
    session.close()