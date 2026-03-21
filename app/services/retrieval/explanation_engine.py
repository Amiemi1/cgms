def explain(query: str, memories: list) -> str:
    if not memories:
        return "No explanation available."

    explanation = "🧠 Why these results:\n\n"

    for m in memories[:3]:
        explanation += f"- '{m.summary}' matched your query\n"

    return explanation