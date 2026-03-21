def apply_natural_language(text: str, dt):
    text = text.lower()

    if "morning" in text:
        return dt.replace(hour=9, minute=0)

    if "afternoon" in text:
        return dt.replace(hour=14, minute=0)

    if "evening" in text:
        return dt.replace(hour=18, minute=0)

    if "night" in text:
        return dt.replace(hour=21, minute=0)

    if "asap" in text:
        from datetime import timedelta
        return dt + timedelta(minutes=30)

    return dt