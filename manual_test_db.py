from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.db.session import SessionLocal
from sqlmodel import select
from app.db.models.memory import Memory

print("TEST DATABASE URL:", settings.DATABASE_URL)

session = SessionLocal()

try:
    memories = session.exec(select(Memory)).all()

    print("TOTAL MEMORIES:", len(memories))

    for m in memories[:10]:
        print("CHAT:", m.chat_id, "|", m.summary)

    print("\n--- SUBTASK CHECK ---")

    for m in memories:
        if m.summary in [
            "Draft key points",
            "Align data and evidence",
            "Review and refine messaging",
            "Gather latest performance data",
            "Identify key trends",
            "Summarize insights"
        ]:
            print(
                m.id,
                "|", m.summary,
                "| status:", m.status,
                "| depends_on:", m.depends_on
            )

finally:
    session.close()