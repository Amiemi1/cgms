from rapidfuzz import fuzz
from datetime import timedelta


SIMILARITY_THRESHOLD = 80  # % similarity
TIME_WINDOW_MINUTES = 60   # 1 hour tolerance


def is_similar_text(text1: str, text2: str) -> bool:
    score = fuzz.ratio(text1.lower(), text2.lower())
    return score >= SIMILARITY_THRESHOLD


def is_same_type(type1: str, type2: str) -> bool:
    return type1 == type2


def is_time_close(time1, time2) -> bool:
    if not time1 or not time2:
        return False

    delta = abs(time1 - time2)
    return delta <= timedelta(minutes=TIME_WINDOW_MINUTES)


def is_duplicate(new_memory, existing_memory) -> bool:
    """
    new_memory: CandidateMemory-like object
    existing_memory: Memory-like object
    """

    # 1. Type must match
    if not is_same_type(new_memory.type, existing_memory.type):
        return False

    # 2. Text similarity
    if not is_similar_text(new_memory.summary, existing_memory.summary):
        return False

    # 3. Time proximity (only if both have time)
    if new_memory.reminder_time and existing_memory.reminder_time:
        if not is_time_close(new_memory.reminder_time, existing_memory.reminder_time):
            return False

    return True


def find_duplicate(new_memory, existing_memories):
    """
    Returns the first duplicate found, else None
    """
    for mem in existing_memories:
        if is_duplicate(new_memory, mem):
            return mem

    return None