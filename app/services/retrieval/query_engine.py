from typing import List

from sqlmodel import Session

from app.db.models.memory import Memory
from app.services.retrieval.vector_search import vector_search
from app.services.llm.llm_service import generate_response


def _build_context(memories: List[Memory]) -> str:
    """
    Build structured memory context for LLM
    """
    if not memories:
        return ""

    return "\n".join([
        f"- {m.summary} (priority: {m.priority}, type: {m.memory_type})"
        for m in memories
    ])


def _fallback_response(memories: List[Memory]) -> str:
    """
    Fallback if LLM fails
    """
    if not memories:
        return "No relevant memories found."

    lines = ["Here are your relevant items:\n"]

    for m in memories[:5]:
        lines.append(f"- {m.summary} (priority: {m.priority})")

    return "\n".join(lines)


def run_query(session: Session, chat_id: int, query: str) -> str:
    """
    Main query execution:
    - semantic retrieval
    - LLM reasoning
    - fallback if needed
    """

    # 🔥 Step 1 — retrieve relevant memories
    memories = vector_search(session, query, chat_id, limit=10)

    if not memories:
        return "No relevant memories found."

    # 🔥 Step 2 — build context
    context = _build_context(memories)

    prompt = f"""
You are an executive assistant helping a user manage tasks and decisions.

User Query:
{query}

Relevant Memories:
{context}

Instructions:
- Identify the most important items
- Prioritize them clearly
- Highlight urgency or risks
- Provide actionable recommendations
- Keep response concise and structured
"""

    # 🔥 Step 3 — call LLM
    response = generate_response(prompt)

    # 🔥 Step 4 — safety fallback
    if not response or response.startswith("LLM Error"):
        return _fallback_response(memories)

    return response