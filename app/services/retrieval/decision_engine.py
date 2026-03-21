from datetime import datetime


def reprioritize(memories):
    now = datetime.now()

    for m in memories:
        if not m.reminder_time:
            continue

        delta = (m.reminder_time - now).total_seconds()

        # 🔥 overdue → highest priority
        if delta < 0:
            m.priority = 100

        # 🔥 due today → very high
        elif delta < 86400:
            m.priority = max(m.priority, 80)

        # 🔥 due soon → medium-high
        elif delta < 172800:
            m.priority = max(m.priority, 60)

    return sorted(memories, key=lambda m: m.priority, reverse=True)


def detect_conflicts(memories):
    conflicts = []

    same_time = {}

    for m in memories:
        if not m.reminder_time:
            continue

        key = m.reminder_time.strftime("%Y-%m-%d %H")

        if key not in same_time:
            same_time[key] = []

        same_time[key].append(m)

    for time, items in same_time.items():
        if len(items) > 1:
            conflicts.append((time, items))

    return conflicts


def suggest_reordering(memories):
    recommendations = []

    for i, m in enumerate(memories[:3]):
        recommendations.append(f"Do first: {m.summary}")

    return recommendations


def generate_interventions(memories):
    interventions = []

    for m in memories:
        if m.priority >= 90:
            interventions.append(f"⚠️ Immediate action required: {m.summary}")

    return interventions