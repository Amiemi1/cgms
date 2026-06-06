def is_valid_memory(summary: str) -> bool:
    """
    Filters out weak or meaningless memories
    """

    if not summary:
        return False

    summary = summary.strip().lower()

    # Reject very short memories
    if len(summary.split()) < 3:
        return False

    # Reject generic verbs
    weak_words = [
        "do",
        "prepare",
        "meeting",
        "task",
        "work"
    ]

    if summary in weak_words:
        return False

    return True