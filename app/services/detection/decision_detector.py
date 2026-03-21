import re

DECISION_KEYWORDS = [
    "decided", "agreed", "approved", "rejected",
    "confirmed", "we will", "we'll", "we are going to"
]


def detect_decision(text: str):
    text_lower = text.lower()

    # Keyword-based detection
    for keyword in DECISION_KEYWORDS:
        if keyword in text_lower:
            return clean_decision(text)

    # Pattern-based detection
    if re.search(r"\b(we decided to|we agreed to|it was decided)\b", text_lower):
        return clean_decision(text)

    return None


def clean_decision(text: str):
    text = text.strip()

    # Remove leading phrases
    text = re.sub(r"^(we\s+decided\s+to\s+)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(we\s+agreed\s+to\s+)", "", text, flags=re.IGNORECASE)

    return text