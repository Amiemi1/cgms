import re


# ------------------------------------------------
# KEYWORD DEFINITIONS
# ------------------------------------------------

TASK_VERBS = [
    "prepare",
    "create",
    "build",
    "write",
    "send",
    "review",
    "update",
    "finish",
    "complete",
    "plan",
    "organize"
]

DECISION_VERBS = [
    "approve",
    "decide",
    "confirm",
    "select",
    "authorize"
]

EVENT_KEYWORDS = [
    "meeting",
    "call",
    "presentation",
    "conference",
    "appointment"
]

DAYS = [
    "monday","tuesday","wednesday","thursday","friday","saturday","sunday"
]


def detect(text):

    lower = text.lower()

    # DECISION
    if any(word in lower for word in DECISION_VERBS):
        return {"type": "decision", "summary": text}

    # TASK
    if any(word in lower for word in TASK_VERBS):
        return {"type": "task", "summary": text}

    # EVENT
    if any(word in lower for word in EVENT_KEYWORDS) or any(day in lower for day in DAYS):
        return {"type": "event", "summary": text}

    return None