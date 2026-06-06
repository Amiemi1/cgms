from sqlmodel import select
from collections import Counter
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.memory_relationship import MemoryRelationship


def generate_executive_briefing(chat_id: int):

    session = SessionLocal()

    try:

        memories = session.exec(
            select(Memory).where(Memory.chat_id == chat_id)
        ).all()

        relationships = session.exec(
            select(MemoryRelationship)
        ).all()

        now = datetime.utcnow()

        events = []
        blocked_tasks = []
        decision_tasks = []

        # ------------------------------------------------
        # UPCOMING EVENTS
        # ------------------------------------------------

        for m in memories:

            if (
                m.memory_type == "event"
                and m.reminder_time
                and m.reminder_time < now + timedelta(hours=24)
            ):

                events.append(m.summary)

        # ------------------------------------------------
        # BLOCKED TASKS
        # ------------------------------------------------

        for task in memories:

            if task.memory_type != "task":
                continue

            resolved = any(
                r.target_memory_id == task.id
                and r.relationship_type == "resolves"
                for r in relationships
            )

            if not resolved:
                blocked_tasks.append(task.summary)

        # ------------------------------------------------
        # DECISIONS REQUIRED
        # ------------------------------------------------

        for rel in relationships:

            if rel.relationship_type == "triggered_by":

                task = next((m for m in memories if m.id == rel.source_memory_id), None)

                if task and task.memory_type == "task":
                    decision_tasks.append(task.summary)

        # ------------------------------------------------
        # WORK FOCUS DETECTION
        # ------------------------------------------------

        words = []

        for m in memories:
            tokens = m.summary.lower().split()

            for t in tokens:
                if len(t) > 4:
                    words.append(t)

        focus = Counter(words).most_common(1)

        focus_text = None
        if focus:
            focus_text = focus[0][0]

        # ------------------------------------------------
        # BUILD BRIEFING
        # ------------------------------------------------

        briefing = "📊 CGMS Executive Briefing\n\n"

        if events:
            briefing += "📅 Upcoming Events\n"
            for e in events:
                briefing += f"• {e}\n"
            briefing += "\n"

        if blocked_tasks:
            briefing += "⚠ Blocked Tasks\n"
            for t in blocked_tasks[:5]:
                briefing += f"• {t}\n"
            briefing += "\n"

        if decision_tasks:
            briefing += "🧠 Tasks Requiring Decisions\n"
            for t in decision_tasks[:5]:
                briefing += f"• {t}\n"
            briefing += "\n"

        if focus_text:
            briefing += f"🔥 Current Focus: {focus_text} related work\n"

        return briefing

    finally:

        session.close()