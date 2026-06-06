# ==============================================================
# STRATEGY ENGINE
# ==============================================================

from sqlmodel import select
from collections import Counter

from app.db.models.memory import Memory


def generate_strategy(session, chat_id, goal):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    if not memories:
        return "No data available for strategy analysis."

    summaries = [m.summary.lower() for m in memories]

    words = []
    for s in summaries:
        words.extend(s.split())

    common = Counter(words).most_common(3)

    focus_topic = common[0][0] if common else "general"

    blocked_tasks = [
        m.summary
        for m in memories
        if m.memory_type == "task" and m.priority and m.priority < 30
    ]

    return {
        "focus_topic": focus_topic,
        "blocked_tasks": blocked_tasks
    }