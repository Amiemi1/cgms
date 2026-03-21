from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, Set


INTENT_MAP = {
    "decision": ["decide", "decision", "agreed", "agree", "chose", "chosen"],
    "task": ["task", "do", "action", "todo", "to do"],
    "event": ["meeting", "call", "event", "session", "appointment"],
}


def normalize(text: str) -> str:
    return text.lower().strip()


def classify_intent(text: str) -> Dict[str, Any]:
    """
    Extract intent from user query.
    """
    t = normalize(text)

    result = {
        "types": set(),     # type: Set[str]
        "time": None        # type: Optional[str]
    }

    # Detect memory type
    for mem_type, words in INTENT_MAP.items():
        for w in words:
            if w in t:
                result["types"].add(mem_type)

    # Smart inference
    if "what should i do" in t:
        result["types"].add("task")

    if "what did we decide" in t:
        result["types"].add("decision")

    if "what meetings" in t:
        result["types"].add("event")

    # Time understanding
    if "today" in t:
        result["time"] = "today"
    elif "tomorrow" in t:
        result["time"] = "tomorrow"
    elif "week" in t:
        result["time"] = "week"

    return result


def resolve_time_filter(label: Optional[str]) -> Optional[Tuple[datetime, datetime]]:
    """
    Convert time keyword into datetime range.
    """
    if not label:
        return None

    now = datetime.now()

    if label == "today":
        start = now
        end = now.replace(hour=23, minute=59, second=59)
        return start, end

    if label == "tomorrow":
        start = now + timedelta(days=1)
        end = start.replace(hour=23, minute=59, second=59)
        return start, end

    if label == "week":
        return now, now + timedelta(days=7)

    return None