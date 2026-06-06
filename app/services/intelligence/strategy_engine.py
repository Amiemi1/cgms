# ==============================================================
# STRATEGIC AWARENESS ENGINE
# ==============================================================

from collections import Counter
from sqlmodel import select

from app.db.models.memory import Memory


def generate_strategy_report(session, chat_id):

    memories = session.exec(
        select(Memory).where(Memory.chat_id == chat_id)
    ).all()

    if not memories:
        return "No strategic insights available."

    words = []

    for m in memories:

        tokens = m.summary.lower().split()

        for token in tokens:

            if len(token) > 4:
                words.append(token)

    counter = Counter(words)

    top = counter.most_common(5)

    response = "🧭 Strategic Focus Areas\n\n"

    for word, count in top:

        response += f"• {word} related work ({count} memories)\n"

    return response