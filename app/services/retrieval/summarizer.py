def summarize(memories: list) -> str:
    if not memories:
        return "Nothing to summarize."

    decisions = [m for m in memories if m.memory_type == "decision"]
    tasks = [m for m in memories if m.memory_type == "task"]
    events = [m for m in memories if m.memory_type == "event"]

    response = "📊 Summary:\n\n"

    if decisions:
        response += "🧠 Decisions:\n"
        for d in decisions:
            response += f"- {d.summary}\n"
        response += "\n"

    if tasks:
        response += "📌 Tasks:\n"
        for t in tasks:
            response += f"- {t.summary}\n"
        response += "\n"

    if events:
        response += "📅 Events:\n"
        for e in events:
            response += f"- {e.summary}\n"
        response += "\n"

    return response