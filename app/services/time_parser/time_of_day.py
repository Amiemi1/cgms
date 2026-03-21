import re


def parse_time_of_day(text: str, dt):
    text = text.lower()

    # 24-hour format (14:30)
    match_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
    if match_24:
        hour = int(match_24.group(1))
        minute = int(match_24.group(2))
        return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # 12-hour format (3pm, 11am)
    match_12 = re.search(r"\b(1[0-2]|0?[1-9])(am|pm)\b", text)
    if match_12:
        hour = int(match_12.group(1))
        period = match_12.group(2)

        if period == "pm" and hour != 12:
            hour += 12
        if period == "am" and hour == 12:
            hour = 0

        return dt.replace(hour=hour, minute=0, second=0, microsecond=0)

    # "at 9"
    match_at = re.search(r"\bat (\d{1,2})\b", text)
    if match_at:
        hour = int(match_at.group(1))
        return dt.replace(hour=hour, minute=0, second=0, microsecond=0)

    return dt