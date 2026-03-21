from datetime import datetime, timedelta


def auto_adjust(memories):
    now = datetime.now()

    for m in memories:

        if not m.reminder_time:
            continue

        delta = (m.reminder_time - now).total_seconds()

        # 🔥 OVERDUE → MAX PRIORITY
        if delta < 0:
            m.priority = 100

        # 🔥 TODAY → HIGH PRIORITY
        elif delta < 86400:
            m.priority = max(m.priority, 80)

        # 🔥 SOON → MEDIUM
        elif delta < 172800:
            m.priority = max(m.priority, 60)

    return memories


def auto_reschedule(memories):
    now = datetime.now()

    updates = []

    for m in memories:

        if not m.reminder_time:
            continue

        delta = (m.reminder_time - now).total_seconds()

        # 🔥 overdue → push forward
        if delta < -3600:
            new_time = now + timedelta(hours=2)
            updates.append((m, new_time))

    return updates