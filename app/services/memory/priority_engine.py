from datetime import datetime


def compute_priority(summary: str, reminder_time=None) -> int:
    text = summary.lower()
    score = 20

    # 🔥 keyword boost
    if "urgent" in text:
        score += 50

    if "asap" in text:
        score += 40

    # 🔥 time-based urgency
    if reminder_time:
        now = datetime.now()
        delta = (reminder_time - now).total_seconds()

        if delta < 0:
            score += 60  # overdue
        elif delta < 86400:
            score += 40  # within 24h
        elif delta < 172800:
            score += 20  # within 48h

    return min(score, 100)