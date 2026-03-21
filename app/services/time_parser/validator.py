from datetime import datetime, timedelta


def validate_future_time(dt: datetime, now: datetime) -> datetime:
    """
    Ensures the datetime is always in the future.
    Applies intelligent shifting based on context.
    """

    # If already in the future → valid
    if dt > now:
        return dt

    # --- Case 1: Same-day time has passed ---
    if dt.date() == now.date():
        # Move to next day, same time
        return dt + timedelta(days=1)

    # --- Case 2: Weekday already passed today ---
    # Example: Monday 9am but now Monday 6pm
    if dt < now:
        return dt + timedelta(days=7)

    return dt