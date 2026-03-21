import re
from datetime import datetime

def parse_absolute(text: str, now):
    text = text.lower()

    # “on the 15th”
    match = re.search(r"(\d{1,2})(st|nd|rd|th)", text)
    if match:
        day = int(match.group(1))

        month = now.month
        year = now.year

        if day < now.day:
            month += 1
            if month > 12:
                month = 1
                year += 1

        return datetime(year, month, day)

    return None