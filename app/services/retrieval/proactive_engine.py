from datetime import datetime


def generate_insights(memories: list) -> str:
    now = datetime.now()

    upcoming = []
    overdue = []

    for m in memories:
        if m.reminder_time:
            delta = (m.reminder_time - now).total_seconds()

            if delta < 0:
                overdue.append(m)
            elif delta < 86400:
                upcoming.append(m)

    response = ""

    if overdue:
        response += "⚠️ Overdue:\n"
        for m in overdue:
            response += f"- {m.summary}\n"
        response += "\n"

    if upcoming:
        response += "⏰ Upcoming (24h):\n"
        for m in upcoming:
            response += f"- {m.summary}\n"

    return response if response else "No immediate insights."