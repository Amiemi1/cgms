from datetime import datetime


def predict_risks(memories, learning_data):
    now = datetime.now()

    risks = []

    for m in memories:
        if not m.reminder_time:
            continue

        delta = (m.reminder_time - now).total_seconds()

        # 🔥 close deadline
        if 0 < delta < 86400:
            risks.append((m, "Due soon"))

        # 🔥 overdue risk
        if delta < 0:
            risks.append((m, "Already overdue"))

    return risks


def predict_behavior_patterns(memories, learning_data):
    delayed_count = 0

    for entry in learning_data:
        if entry.action == "delayed":
            delayed_count += 1

    insights = []

    if delayed_count > 3:
        insights.append("You tend to delay tasks frequently")

    return insights


def recommend_actions(memories):
    # sort by urgency + priority
    sorted_memories = sorted(
        memories,
        key=lambda m: (
            m.priority,
            m.reminder_time or datetime.max
        ),
        reverse=True
    )

    recommendations = []

    for m in sorted_memories[:3]:
        recommendations.append(f"Focus on: {m.summary}")

    return recommendations