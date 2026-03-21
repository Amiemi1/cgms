def apply_defaults(dt):
    if dt.hour == 0 and dt.minute == 0:
        return dt.replace(hour=9, minute=0)
    return dt