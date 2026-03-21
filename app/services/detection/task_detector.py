import re

TASK_KEYWORDS = [
    "send", "submit", "prepare", "review", "call", "schedule",
    "complete", "finish", "update", "check", "follow up",
    "remind", "email", "deliver", "organize"
]


def detect_task(text: str):
    text_lower = text.lower()

    # ANY sentence with a verb-like structure
    verbs = [
        "send", "call", "review", "prepare", "submit",
        "complete", "check", "follow", "email"
    ]

    for v in verbs:
        if v in text_lower:
            return text

    # fallback: anything with "tomorrow" is likely a task
    if "tomorrow" in text_lower:
        return text

    return None


def clean_task(text: str):
    """
    Clean unnecessary prefixes
    """
    text = text.strip()

    # Remove 'please'
    text = re.sub(r"^please\s+", "", text, flags=re.IGNORECASE)

    return text