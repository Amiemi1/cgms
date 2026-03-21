import os


def generate_response(prompt: str) -> str:
    """
    Simple LLM wrapper (can upgrade later).
    For now: rule-based fallback.
    """

    # 🔥 placeholder logic (safe + offline)
    # You can later replace with OpenAI or local LLM

    return f"[AI Insight]\n{prompt}"