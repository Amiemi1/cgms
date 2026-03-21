from datetime import datetime


def analyze(memories):
    now = datetime.now()

    urgent = []
    today = []
    overdue = []

    for m in memories:
        if m.reminder_time:
            delta = (m.reminder_time - now).total_seconds()

            if delta < 0:
                overdue.append(m)
            elif delta < 86400:
                today.append(m)

        if m.priority >= 70:
            urgent.append(m)

    return {
        "urgent": urgent,
        "today": today,
        "overdue": overdue
    }