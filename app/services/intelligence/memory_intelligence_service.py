# ==============================================================
# MEMORY INTELLIGENCE SERVICE
# ==============================================================

"""
Ranks memories using:
• keyword matching
• semantic matching
• context awareness
• memory-type weighting
"""

# --------------------------------------------------------------
# SEMANTIC WORD GROUPS
# --------------------------------------------------------------

SEMANTIC_GROUPS = {

    "prepare": ["preparation", "plan", "planning", "ready"],

    "meeting": ["discussion", "session", "gathering"],

    "decision": ["approve", "approval", "decide"],

    "distributor": ["partner", "dealer"],

}


# --------------------------------------------------------------
# SEMANTIC MATCH
# --------------------------------------------------------------

def semantic_match(word, summary):

    for key, words in SEMANTIC_GROUPS.items():

        if word == key or word in words:

            if key in summary:
                return True

            for w in words:
                if w in summary:
                    return True

    return False


# --------------------------------------------------------------
# SCORE MEMORY
# --------------------------------------------------------------

def score_memory(memory, query, context=None):

    score = 0

    q = query.lower()
    summary = memory.summary.lower()

    words = q.split()

    # ----------------------------------------------------------
    # KEYWORD + SEMANTIC MATCH
    # ----------------------------------------------------------

    for word in words:

        if word in summary:
            score += 2

        elif semantic_match(word, summary):
            score += 2


    # ----------------------------------------------------------
    # CONTEXT BOOST
    # ----------------------------------------------------------

    if context and context.lower() in summary:
        score += 3


    # ----------------------------------------------------------
    # INTENT DETECTION
    # ----------------------------------------------------------

    if "prepare" in q or "preparation" in q:

        if memory.memory_type == "task":
            score += 5
        else:
            score -= 1


    if "meeting" in q:

        if memory.memory_type in ["task", "event"]:
            score += 6

        elif memory.memory_type == "task":
            score += 4
        
        else:
            score -= 3


    if "when" in q or "schedule" in q:

        if memory.memory_type == "event":
            score += 3


    if "decision" in q or "approve" in q:

        if memory.memory_type == "decision":
            score += 3


    # ----------------------------------------------------------
    # MEMORY IMPORTANCE WEIGHTING
    # ----------------------------------------------------------

    importance_weights = {
        "decision": 4,
        "insight": 3,
        "task": 2,
        "event": 1
    }

    score += importance_weights.get(memory.memory_type, 0)

    return score


# --------------------------------------------------------------
# RANK MEMORIES
# --------------------------------------------------------------

def rank_memories(memories, query, context=None):

    ranked = sorted(
        memories,
        key=lambda m: score_memory(m, query, context),
        reverse=True
    )

    # ----------------------------------------------------------
    # REMOVE DUPLICATES
    # ----------------------------------------------------------

    unique = {}

    for m in ranked:

        if m.summary not in unique:
            unique[m.summary] = m

    results = list(unique.values())


    # ----------------------------------------------------------
    # DEBUG OUTPUT
    # ----------------------------------------------------------

    for m in results[:10]:

        print(
            f"[DEBUG] INTELLIGENCE | id={m.id} "
            f"| type={m.memory_type} "
            f"| score={score_memory(m, query, context)} "
            f"| summary={m.summary}"
        )

    return results[:10]