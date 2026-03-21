from datetime import datetime

# Keyword signals
HIGH_PRIORITY_KEYWORDS = [
    "urgent", "asap", "immediately", "now", "today"
]

MEDIUM_PRIORITY_KEYWORDS = [
    "soon", "important", "priority"
]


def keyword_score(text: str) -> int:
    text = text.lower()

    for word in HIGH_PRIORITY_KEYWORDS:
        if word in text:
            return 30

    for word in MEDIUM_PRIORITY_KEYWORDS:
        if word in text:
            return 20

    return 0


def time_urgency_score(reminder_time) -> int:
    if not reminder_time:
        return 0

    now = datetime.now()
    delta = (reminder_time - now).total_seconds()

    # Convert to hours
    hours = delta / 3600

    if hours <= 1:
        return 50
    elif hours <= 6:
        return 40
    elif hours <= 24:
        return 30
    elif hours <= 72:
        return 20
    else:
        return 10


def compute_priority(memory) -> int:
    """
    memory: CandidateMemory-like object
    """

    score = 20  # baseline

    # Add keyword signal
    score += keyword_score(memory.summary)

    # Add time urgency
    score += time_urgency_score(memory.reminder_time)

    return min(score, 100)