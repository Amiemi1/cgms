# ==============================================================
# MEMORY IMPORTANCE ENGINE
# ==============================================================

from collections import Counter


def calculate_memory_importance(memory, related_count=0):

    score = 0

    # ---------------------------------
    # Memory Type Weight
    # ---------------------------------

    if memory.memory_type == "decision":
        score += 5

    elif memory.memory_type == "event":
        score += 4

    elif memory.memory_type == "task":
        score += 3

    # ---------------------------------
    # Relationship Influence
    # ---------------------------------

    score += related_count

    # ---------------------------------
    # Keyword Importance
    # ---------------------------------

    keywords = [
        "meeting",
        "presentation",
        "decision",
        "approve",
        "plan",
        "deadline",
        "launch"
    ]

    text = memory.summary.lower()

    for k in keywords:

        if k in text:
            score += 1

    # ---------------------------------
    # Cap score
    # ---------------------------------

    if score > 10:
        score = 10

    return score