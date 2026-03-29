from typing import Optional


DECISION_KEYWORDS = [
    "decide",
    "decision",
    "approve",
    "approved",
    "reject",
    "rejected",
    "choose",
    "chosen",
    "select",
    "selected",
    "agree",
    "agreed",
    "finalize",
    "finalise"
]


def detect_decision(text: str) -> Optional[str]:
    """
    Detect decision statements from user input.
    """

    if not text:
        return None

    lower_text = text.lower()

    for keyword in DECISION_KEYWORDS:
        if keyword in lower_text:
            return text

    return None