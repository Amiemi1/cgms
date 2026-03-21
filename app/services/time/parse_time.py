from datetime import datetime, timedelta
import re


def parse_time(text: str):
    print("📥 INPUT TEXT:", text)

    text = text.lower()
    now = datetime.now()

    # -------------------------
    # 1. HANDLE "tomorrow"
    # -------------------------
    if "tomorrow" in text:
        base_date = now + timedelta(days=1)
    else:
        base_date = now

    # -------------------------
    # 2. HANDLE TIME (HH:MM)
    # -------------------------
    match = re.search(r'(\d{1,2}):(\d{2})', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        result = base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        print("✅ PARSED TIME:", result)
        return result

    # -------------------------
    # 3. HANDLE "at 7" (no minutes)
    # -------------------------
    match = re.search(r'at (\d{1,2})\b', text)
    if match:
        hour = int(match.group(1))

        result = base_date.replace(hour=hour, minute=0, second=0, microsecond=0)

        print("✅ PARSED TIME:", result)
        return result

    print("❌ NO TIME FOUND")
    return None