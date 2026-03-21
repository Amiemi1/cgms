from typing import List
from sqlmodel import Session, select

from app.db.models.memory import Memory
from app.services.retrieval.vector_search import vector_search


# =========================
# SUMMARY
# =========================
def generate_summary(session: Session, chat_id: int) -> str:

    memories = session.exec(
        select(Memory).where(
            Memory.chat_id == chat_id,
            Memory.status == "active"
        )
    ).all()

    if not memories:
        return "No items found."

    # simple priority sort
    memories = sorted(memories, key=lambda x: x.priority, reverse=True)

    lines = ["📊 Summary\n"]

    for m in memories[:5]:
        lines.append(f"- {m.summary} (priority: {m.priority})")

    return "\n".join(lines)


# =========================
# LIST
# =========================
def generate_list(session: Session, chat_id: int) -> str:

    memories = session.exec(
        select(Memory).where(
            Memory.chat_id == chat_id,
            Memory.status == "active"
        )
    ).all()

    if not memories:
        return "No items available."

    grouped = {"task": [], "event": [], "decision": []}

    for m in memories:
        grouped.setdefault(m.memory_type, []).append(m)

    lines = ["📋 Your Items\n"]

    for k, items in grouped.items():
        if items:
            lines.append(f"\n{k.upper()}:")
            for m in items:
                lines.append(f"- {m.summary}")

    return "\n".join(lines)


# =========================
# SEARCH
# =========================
def generate_search(session: Session, chat_id: int, query: str) -> str:

    memories = vector_search(session, query, chat_id, limit=10)

    if not memories:
        return "No matching items found."

    lines = ["🔍 Search Results\n"]

    for m in memories:
        lines.append(f"- {m.summary} (priority: {m.priority})")

    return "\n".join(lines)