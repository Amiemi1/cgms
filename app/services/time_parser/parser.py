from datetime import datetime, timedelta
import re


# =========================
# HELPERS
# =========================

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


TIME_OF_DAY = {
    "morning": 9,
    "afternoon": 14,
    "evening": 18,
    "night": 21,
}


# =========================
# TIME PARSING FUNCTIONS
# =========================

def parse_time_of_day(text: str):
    for key, hour in TIME_OF_DAY.items():
        if key in text:
            return hour
    return None


def parse_explicit_time(text: str):
    """
    Extract explicit time like:
    - 9am
    - 14:30
    """

    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text)

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)

    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0

    return hour, minute


def parse_relative_day(text: str, now: datetime):
    if "today" in text:
        return now

    if "tomorrow" in text:
        return now + timedelta(days=1)

    return None


def parse_weekday(text: str, now: datetime):
    for day, idx in WEEKDAYS.items():
        if day in text:

            today_idx = now.weekday()
            diff = idx - today_idx

            if diff <= 0:
                diff += 7

            return now + timedelta(days=diff)

    return None


def parse_relative_time(text: str, now: datetime):
    """
    Handles:
    - in 2 hours
    - in 30 minutes
    """

    match = re.search(r'in (\d+)\s*(hour|hours|minute|minutes)', text)

    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if "hour" in unit:
        return now + timedelta(hours=value)

    if "minute" in unit:
        return now + timedelta(minutes=value)

    return None


# =========================
# MAIN PARSER
# =========================

def extract_time(text: str):
    """
    Main time extraction function.
    """

    if not text:
        return None

    text = text.lower()
    now = datetime.now()

    # 🔹 1. Relative time (highest priority)
    relative_time = parse_relative_time(text, now)
    if relative_time:
        return relative_time

    # 🔹 2. Relative day (today / tomorrow)
    base_date = parse_relative_day(text, now)

    # 🔹 3. Weekday (next monday)
    if not base_date:
        base_date = parse_weekday(text, now)

    # 🔹 Default → today
    if not base_date:
        base_date = now

    # 🔹 4. Explicit time
    explicit_time = parse_explicit_time(text)

    if explicit_time:
        hour, minute = explicit_time
    else:
        # 🔹 fallback to time of day
        hour = parse_time_of_day(text)
        minute = 0

    # 🔹 Final datetime
    if hour is not None:
        return base_date.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

    return None


# =========================
# SAFE WRAPPER
# =========================

def extract_time_safe(text: str):
    """
    Safe wrapper that never crashes.
    """

    try:
        dt = extract_time(text)

        if not dt:
            return None

        return dt.replace(second=0, microsecond=0)

    except Exception:
        return None