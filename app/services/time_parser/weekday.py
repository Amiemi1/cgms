import re
from datetime import timedelta

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def parse_weekday(text: str, now):
    text = text.lower()

    for day_name, target_day in WEEKDAYS.items():
        if re.search(rf"\b{day_name}\b", text):
            current_day = now.weekday()
            delta = target_day - current_day

            # Handle "next"
            if "next" in text:
                delta = delta + 7 if delta <= 0 else delta + 7

            # Handle "this"
            elif "this" in text:
                if delta < 0:
                    delta += 7

            # Default → next occurrence
            else:
                if delta <= 0:
                    delta += 7

            return now + timedelta(days=delta)

    return None