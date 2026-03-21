from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_memory(query: str, memory):
    base = similarity(query, memory.summary)

    # 🔥 boost by type match
    if memory.memory_type in query:
        base += 0.2

    # 🔥 boost recent
    if memory.created_at:
        base += 0.1

    # 🔥 boost priority
    base += memory.priority / 200

    return round(base, 3)