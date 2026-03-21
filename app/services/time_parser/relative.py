import re
from datetime import timedelta

def parse_relative(text: str, now):
    text = text.lower()

    # in X minutes/hours/days
    match = re.search(r"in (\d+) (minute|minutes|hour|hours|day|days)", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if "minute" in unit:
            return now + timedelta(minutes=value)
        elif "hour" in unit:
            return now + timedelta(hours=value)
        elif "day" in unit:
            return now + timedelta(days=value)

    # tomorrow
    if "tomorrow" in text:
        return now + timedelta(days=1)

    return None