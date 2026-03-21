from typing import List

from app.db.models.memory import Memory
from app.services.llm.llm_service import generate_response


def _build_context(memories: List[Memory]) -> str:
    """
    Build structured context for briefing
    """
    return "\n".join([
        f"- {m.summary} (priority: {m.priority}, type: {m.memory_type})"
        for m in memories
    ])


def _fallback_briefing(memories: List[Memory]) -> str:
    """
    Fallback briefing if LLM fails
    """
    if not memories:
        return "No data available for briefing."

    lines = ["📊 Daily Briefing\n"]

    # simple priority sort
    sorted_memories = sorted(memories, key=lambda x: x.priority, reverse=True)

    lines.append("\nTop Items:")
    for m in sorted_memories[:5]:
        lines.append(f"- {m.summary} (priority: {m.priority})")

    return "\n".join(lines)


def generate_executive_briefing(memories: List[Memory]) -> str:
    """
    Generate intelligent daily briefing using LLM
    """

    if not memories:
        return "No data available for briefing."

    context = _build_context(memories)

    prompt = f"""
You are an executive assistant preparing a daily briefing.

Here are the user's current items:
{context}

Generate a structured briefing with:

1. Top Priorities (most important tasks)
2. Risks (missed deadlines, delays, etc.)
3. Recommendations (what to do next)

Keep it concise, clear, and actionable.
"""

    response = generate_response(prompt)

    # 🔥 fallback if LLM fails
    if not response or response.startswith("LLM Error"):
        return _fallback_briefing(memories)

    return response