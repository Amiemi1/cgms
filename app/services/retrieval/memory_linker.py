def link_memories(memories: list) -> str:
    if not memories:
        return "No linked insights."

    decisions = [m for m in memories if m.memory_type == "decision"]
    tasks = [m for m in memories if m.memory_type == "task"]

    response = "🔗 Related Insights:\n\n"

    for d in decisions:
        response += f"Decision: {d.summary}\n"

        related_tasks = [
            t for t in tasks
            if any(word in t.summary.lower() for word in d.summary.lower().split())
        ]

        for t in related_tasks:
            response += f"  ↳ Task: {t.summary}\n"

        response += "\n"

    return response