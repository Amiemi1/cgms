import re

EVENT_KEYWORDS = [
    "meeting", "call", "appointment", "event",
    "conference", "session", "training", "interview"
]


TIME_HINTS = [
    "today", "tomorrow", "next", "at", "on", "by",
    "morning", "afternoon", "evening"
]


def detect_event(text: str):
    text_lower = text.lower()

    # Must contain event keyword
    has_event_word = any(word in text_lower for word in EVENT_KEYWORDS)

    # Must contain time signal
    has_time_hint = any(word in text_lower for word in TIME_HINTS)

    if has_event_word and has_time_hint:
        return clean_event(text)

    # Pattern fallback (e.g. "meeting tomorrow at 3")
    if re.search(r"\b(meeting|call)\b.*\b(today|tomorrow|at)\b", text_lower):
        return clean_event(text)

    return None


def clean_event(text: str):
    text = text.strip()

    # Remove unnecessary prefixes
    text = re.sub(r"^event:\s*", "", text, flags=re.IGNORECASE)

    return text